/**
 * REBORNFENIX — mint_batch.js
 * Cunha 22.222 cNFTs em batch usando Metaplex Bubblegum.
 * Este é o passo 3 de 3. Corre DEPOIS de create_merkle_tree.js.
 *
 * Funcionalidades:
 *   - Lê metadata de ../metadata/generated/
 *   - Cunha em grupos de 10 com pausa entre grupos
 *   - Retomável: guarda progresso em mint_progress.json
 *   - Cada NFT vai para a coleção definida em collection_address.json
 *
 * Uso:
 *   SOLANA_NETWORK=devnet node mint_batch.js              # cunha tudo
 *   SOLANA_NETWORK=devnet node mint_batch.js --start=100  # começa no #100
 *   SOLANA_NETWORK=devnet node mint_batch.js --end=50     # cunha só até #50
 */

import { createUmi } from "@metaplex-foundation/umi-bundle-defaults";
import {
  mintToCollectionV1,
  mplBubblegum,
  parseLeafFromMintToCollectionV1Transaction,
} from "@metaplex-foundation/mpl-bubblegum";
import {
  createSignerFromKeypair,
  signerIdentity,
  publicKey as umiPublicKey,
} from "@metaplex-foundation/umi";
import { base58 } from "@metaplex-foundation/umi/serializers";
import {
  readFileSync,
  writeFileSync,
  existsSync,
  readdirSync,
} from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import "dotenv/config";

// ─────────────────────────────────────────────
// Configuração
// ─────────────────────────────────────────────
const __dirname = dirname(fileURLToPath(import.meta.url));

const NETWORK = process.env.SOLANA_NETWORK || "devnet";
const RPC_URLS = {
  devnet: "https://api.devnet.solana.com",
  "mainnet-beta": "https://api.mainnet-beta.solana.com",
};

const BATCH_SIZE = 10;         // NFTs por batch
const DELAY_ENTRE_BATCHES = 3000;  // ms entre batches (evita rate limiting)
const DELAY_ENTRE_NFTS = 500;      // ms entre cada NFT no batch
const MAX_RETRIES = 3;              // tentativas por NFT em caso de erro
const RETRY_DELAY = 5000;          // ms de espera entre retries

const METADATA_DIR = join(__dirname, "../metadata/generated");
const PROGRESS_FILE = join(__dirname, "mint_progress.json");
const COLLECTION_FILE = join(__dirname, "collection_address.json");
const TREE_FILE = join(__dirname, "tree_address.json");

// ─────────────────────────────────────────────
// Parse de argumentos da linha de comando
// ─────────────────────────────────────────────
function parseArgs() {
  const args = process.argv.slice(2);
  const result = { start: null, end: null };
  for (const arg of args) {
    if (arg.startsWith("--start=")) result.start = parseInt(arg.split("=")[1]);
    if (arg.startsWith("--end=")) result.end = parseInt(arg.split("=")[1]);
  }
  return result;
}

// ─────────────────────────────────────────────
// Gestão de progresso (retomável)
// ─────────────────────────────────────────────
function carregarProgresso() {
  if (!existsSync(PROGRESS_FILE)) {
    return {
      mintados: [],
      falhados: [],
      ultimoIndex: -1,
      totalMintados: 0,
      totalFalhados: 0,
      iniciado: new Date().toISOString(),
    };
  }
  return JSON.parse(readFileSync(PROGRESS_FILE, "utf8"));
}

function guardarProgresso(progresso) {
  writeFileSync(PROGRESS_FILE, JSON.stringify(progresso, null, 2));
}

// ─────────────────────────────────────────────
// Carregar ficheiros de metadata
// ─────────────────────────────────────────────
function carregarMetadataFiles() {
  if (!existsSync(METADATA_DIR)) {
    console.error(`\n❌ Directório de metadata não encontrado: ${METADATA_DIR}`);
    console.error("   Corre primeiro: cd ../metadata && python metadata_generator.py\n");
    process.exit(1);
  }

  const files = readdirSync(METADATA_DIR)
    .filter((f) => f.endsWith(".json"))
    .sort((a, b) => {
      // Ordenar numericamente: 1.json, 2.json, ..., 22222.json
      const numA = parseInt(a.replace(".json", ""));
      const numB = parseInt(b.replace(".json", ""));
      return numA - numB;
    });

  if (files.length === 0) {
    console.error(`\n❌ Nenhum ficheiro JSON encontrado em ${METADATA_DIR}`);
    console.error("   Corre primeiro: cd ../metadata && python metadata_generator.py\n");
    process.exit(1);
  }

  console.log(`   📁 ${files.length} ficheiros de metadata encontrados`);
  return files;
}

// ─────────────────────────────────────────────
// Cunhar um único NFT (com retry)
// ─────────────────────────────────────────────
async function cunharNFT(umi, params, nftIndex, tentativa = 1) {
  const {
    merkleTree,
    collectionMint,
    metadata,
    creatorAddress,
  } = params;

  try {
    const { signature } = await mintToCollectionV1(umi, {
      leafOwner: umiPublicKey(creatorAddress),
      merkleTree: umiPublicKey(merkleTree),
      collectionMint: umiPublicKey(collectionMint),
      metadata: {
        name: metadata.name,
        symbol: metadata.symbol || "RBFX",
        uri: metadata.uri || metadata.image,
        sellerFeeBasisPoints: metadata.seller_fee_basis_points || 500,
        collection: {
          key: umiPublicKey(collectionMint),
          verified: false, // verificado automaticamente pelo Bubblegum
        },
        creators: [
          {
            address: umiPublicKey(creatorAddress),
            verified: true,
            share: 100,
          },
        ],
      },
    }).sendAndConfirm(umi, {
      confirm: { commitment: "confirmed" },
      send: { skipPreflight: true }, // mais rápido em batch
    });

    const txSig = base58.serialize(signature);
    return { sucesso: true, signature: txSig, nftIndex };
  } catch (err) {
    if (tentativa < MAX_RETRIES) {
      console.warn(
        `   ⚠️  NFT #${nftIndex} falhou (tentativa ${tentativa}/${MAX_RETRIES}): ${err.message.slice(0, 80)}`
      );
      await new Promise((r) => setTimeout(r, RETRY_DELAY));
      return cunharNFT(umi, params, nftIndex, tentativa + 1);
    }
    return { sucesso: false, erro: err.message, nftIndex };
  }
}

// ─────────────────────────────────────────────
// Formatar tempo restante
// ─────────────────────────────────────────────
function formatarTempo(ms) {
  const segundos = Math.floor(ms / 1000);
  const minutos = Math.floor(segundos / 60);
  const horas = Math.floor(minutos / 60);
  if (horas > 0) return `${horas}h ${minutos % 60}min`;
  if (minutos > 0) return `${minutos}min ${segundos % 60}s`;
  return `${segundos}s`;
}

// ─────────────────────────────────────────────
// Script principal
// ─────────────────────────────────────────────
async function mintarEmBatch() {
  console.log("\n╔══════════════════════════════════════════════════════════╗");
  console.log("║         REBORNFENIX — Minting em Batch (Passo 3/3)      ║");
  console.log("╚══════════════════════════════════════════════════════════╝\n");

  const { start: argStart, end: argEnd } = parseArgs();

  // Verificar pré-requisitos
  if (!existsSync(COLLECTION_FILE)) {
    console.error("❌ collection_address.json não encontrado. Corre: node deploy_collection.js");
    process.exit(1);
  }
  if (!existsSync(TREE_FILE)) {
    console.error("❌ tree_address.json não encontrado. Corre: node create_merkle_tree.js");
    process.exit(1);
  }

  const { collectionMint, network: colNet } = JSON.parse(readFileSync(COLLECTION_FILE, "utf8"));
  const { treeAddress, network: treeNet } = JSON.parse(readFileSync(TREE_FILE, "utf8"));

  console.log(`✅ Coleção   : ${collectionMint}`);
  console.log(`✅ Árvore    : ${treeAddress}`);

  if (colNet !== NETWORK || treeNet !== NETWORK) {
    console.warn(`\n⚠️  AVISO: Rede dos ficheiros (${colNet}/${treeNet}) difere de SOLANA_NETWORK (${NETWORK})`);
  }

  // Carregar metadata
  console.log("\n📁 A carregar ficheiros de metadata...");
  const metadataFiles = carregarMetadataFiles();

  // Carregar progresso anterior
  const progresso = carregarProgresso();
  const mintadosSet = new Set(progresso.mintados.map((m) => m.index));

  console.log(`\n📊 Estado actual:`);
  console.log(`   Total de NFTs       : ${metadataFiles.length.toLocaleString()}`);
  console.log(`   Já mintados         : ${progresso.totalMintados.toLocaleString()}`);
  console.log(`   Falhados            : ${progresso.totalFalhados}`);
  console.log(`   Por cunhar          : ${(metadataFiles.length - progresso.totalMintados).toLocaleString()}`);

  // Determinar range
  const idxStart = argStart !== null ? argStart - 1 : 0;
  const idxEnd = argEnd !== null ? argEnd - 1 : metadataFiles.length - 1;
  const filesToProcess = metadataFiles.slice(idxStart, idxEnd + 1);

  console.log(`\n   Intervalo a cunhar : #${idxStart + 1} → #${idxEnd + 1} (${filesToProcess.length} NFTs)`);

  // Carregar chave privada e inicializar UMI
  const privateKeyBase58 = process.env.SOLANA_PRIVATE_KEY;
  if (!privateKeyBase58) {
    console.error("\n❌ SOLANA_PRIVATE_KEY não definida no .env\n");
    process.exit(1);
  }

  const rpcUrl = RPC_URLS[NETWORK];
  const umi = createUmi(rpcUrl).use(mplBubblegum());

  let keypair;
  try {
    const privateKeyBytes = base58.deserialize(privateKeyBase58)[0];
    keypair = umi.eddsa.createKeypairFromSecretKey(privateKeyBytes);
  } catch (err) {
    console.error(`\n❌ Chave privada inválida: ${err.message}\n`);
    process.exit(1);
  }

  const signer = createSignerFromKeypair(umi, keypair);
  umi.use(signerIdentity(signer));

  const creatorAddress = keypair.publicKey;
  console.log(`\n🔐 Carteira: ${creatorAddress}`);

  // Filtrar os já mintados
  const pendentes = filesToProcess.filter((_, i) => {
    const globalIndex = idxStart + i;
    return !mintadosSet.has(globalIndex);
  });

  if (pendentes.length === 0) {
    console.log("\n✅ Todos os NFTs neste intervalo já foram mintados!");
    console.log(`   Mintados: ${progresso.totalMintados}`);
    return;
  }

  console.log(`\n🚀 A iniciar minting de ${pendentes.length} NFTs em batches de ${BATCH_SIZE}...`);
  const tempoEstimado =
    Math.ceil(pendentes.length / BATCH_SIZE) *
    (BATCH_SIZE * DELAY_ENTRE_NFTS + DELAY_ENTRE_BATCHES);
  console.log(`   Tempo estimado: ${formatarTempo(tempoEstimado)}\n`);

  const inicio = Date.now();
  let mintadosNestaSessao = 0;
  let falhadosNestaSessao = 0;

  // Processar em batches
  for (let batchStart = 0; batchStart < pendentes.length; batchStart += BATCH_SIZE) {
    const batch = pendentes.slice(batchStart, batchStart + BATCH_SIZE);
    const batchNum = Math.floor(batchStart / BATCH_SIZE) + 1;
    const totalBatches = Math.ceil(pendentes.length / BATCH_SIZE);

    console.log(`\n📦 Batch ${batchNum}/${totalBatches} (${batch.length} NFTs)`);

    const resultados = await Promise.allSettled(
      batch.map(async (filename, batchIdx) => {
        const globalIndex = filesToProcess.indexOf(filename) + idxStart;

        // Pausa escalonada para evitar hits simultâneos
        await new Promise((r) => setTimeout(r, batchIdx * DELAY_ENTRE_NFTS));

        // Carregar metadata do ficheiro
        const metadataPath = join(METADATA_DIR, filename);
        let metadata;
        try {
          metadata = JSON.parse(readFileSync(metadataPath, "utf8"));
        } catch (err) {
          return { sucesso: false, erro: `Erro ao ler ${filename}: ${err.message}`, nftIndex: globalIndex };
        }

        // Verificar URI do metadata (deve estar no IPFS)
        if (!metadata.uri && !metadata.image) {
          return {
            sucesso: false,
            erro: `NFT #${globalIndex + 1} sem URI de metadata`,
            nftIndex: globalIndex,
          };
        }

        const resultado = await cunharNFT(
          umi,
          { merkleTree: treeAddress, collectionMint, metadata, creatorAddress },
          globalIndex + 1
        );

        if (resultado.sucesso) {
          process.stdout.write(`   ✅ #${globalIndex + 1} ${metadata.name || filename}\n`);
        } else {
          process.stdout.write(`   ❌ #${globalIndex + 1} FALHOU: ${resultado.erro?.slice(0, 60)}\n`);
        }

        return resultado;
      })
    );

    // Processar resultados
    for (const result of resultados) {
      const res = result.status === "fulfilled" ? result.value : { sucesso: false, erro: result.reason?.message };
      if (res.sucesso) {
        progresso.mintados.push({
          index: res.nftIndex - 1,
          signature: res.signature,
          timestamp: new Date().toISOString(),
        });
        progresso.totalMintados++;
        mintadosNestaSessao++;
      } else {
        progresso.falhados.push({
          index: res.nftIndex,
          erro: res.erro,
          timestamp: new Date().toISOString(),
        });
        progresso.totalFalhados++;
        falhadosNestaSessao++;
      }
    }

    progresso.ultimoIndex = batchStart + batch.length - 1;
    guardarProgresso(progresso);

    // Estatísticas do batch
    const elapsed = Date.now() - inicio;
    const rate = mintadosNestaSessao / (elapsed / 1000 / 60); // NFTs por minuto
    const remaining = pendentes.length - batchStart - batch.length;
    const etaMs = remaining > 0 && rate > 0 ? (remaining / rate) * 60 * 1000 : 0;

    console.log(
      `   ⏱  Ritmo: ${rate.toFixed(1)} NFTs/min | ` +
      `Restam: ${remaining} | ` +
      `ETA: ${etaMs > 0 ? formatarTempo(etaMs) : "—"}`
    );

    // Pausa entre batches (excepto o último)
    if (batchStart + BATCH_SIZE < pendentes.length) {
      await new Promise((r) => setTimeout(r, DELAY_ENTRE_BATCHES));
    }
  }

  // Sumário final
  const totalElapsed = Date.now() - inicio;
  console.log("\n╔══════════════════════════════════════════════════════════╗");
  console.log("║                   SUMÁRIO DO MINTING                    ║");
  console.log("╠══════════════════════════════════════════════════════════╣");
  console.log(`║  Mintados nesta sessão : ${mintadosNestaSessao.toString().padEnd(31)}║`);
  console.log(`║  Falhados nesta sessão : ${falhadosNestaSessao.toString().padEnd(31)}║`);
  console.log(`║  Total mintados        : ${progresso.totalMintados.toString().padEnd(31)}║`);
  console.log(`║  Tempo total           : ${formatarTempo(totalElapsed).padEnd(31)}║`);
  console.log("╚══════════════════════════════════════════════════════════╝");

  if (falhadosNestaSessao > 0) {
    console.log(`\n⚠️  ${falhadosNestaSessao} NFTs falharam. Para re-tentar apenas os falhados:`);
    console.log("   Verifica mint_progress.json → campo 'falhados'");
    console.log("   Podes usar --start= e --end= para re-cunhar intervalos específicos.\n");
  }

  if (progresso.totalMintados >= metadataFiles.length) {
    console.log("\n🎉 TODOS OS 22.222 NFTs FORAM MINTADOS COM SUCESSO!");
    console.log("\n   Próximos passos:");
    console.log("   1. Verifica a coleção no Magic Eden / Tensor");
    console.log("   2. Segue o setup_magic_eden.md para configurar a venda");
    console.log(`   3. Coleção: https://magiceden.io/marketplace/${collectionMint}\n`);
  }
}

mintarEmBatch().catch((err) => {
  console.error("\n💥 Erro inesperado:", err.message);
  console.error(err.stack);
  process.exit(1);
});
