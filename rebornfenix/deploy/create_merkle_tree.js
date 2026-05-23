/**
 * REBORNFENIX — create_merkle_tree.js
 * Cria a Merkle Tree para NFTs comprimidos (cNFTs) via Metaplex Bubblegum.
 * Este é o passo 2 de 3. Corre DEPOIS de deploy_collection.js.
 *
 * Parâmetros escolhidos:
 *   maxDepth    = 20  → suporta até 1.048.576 nós (suficiente para 22.222)
 *   maxBufferSize = 64 → boa taxa de concorrência para minting em batch
 *   canopyDepth = 14  → equilibra custo vs tamanho da prova (proof)
 *
 * Uso:
 *   SOLANA_NETWORK=devnet node create_merkle_tree.js       # teste
 *   SOLANA_NETWORK=mainnet-beta node create_merkle_tree.js # produção
 */

import { createUmi } from "@metaplex-foundation/umi-bundle-defaults";
import {
  createTree,
  mplBubblegum,
} from "@metaplex-foundation/mpl-bubblegum";
import {
  createSignerFromKeypair,
  signerIdentity,
  generateSigner,
} from "@metaplex-foundation/umi";
import { base58 } from "@metaplex-foundation/umi/serializers";
import {
  Connection,
  LAMPORTS_PER_SOL,
  PublicKey,
} from "@solana/web3.js";
import { readFileSync, writeFileSync, existsSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import "dotenv/config";

// ─────────────────────────────────────────────
// Configuração da Merkle Tree
// ─────────────────────────────────────────────
const __dirname = dirname(fileURLToPath(import.meta.url));

const NETWORK = process.env.SOLANA_NETWORK || "devnet";
const RPC_URLS = {
  devnet: "https://api.devnet.solana.com",
  "mainnet-beta": "https://api.mainnet-beta.solana.com",
};

// Parâmetros da árvore — NÃO ALTERES sem calcular o custo primeiro!
const TREE_CONFIG = {
  maxDepth: 20,        // 2^20 = 1.048.576 slots disponíveis
  maxBufferSize: 64,   // concorrência de transacções simultâneas
  canopyDepth: 14,     // profundidade do canopy (armazena parte da prova on-chain)
};

const TOTAL_NFTS = 22_222;

// ─────────────────────────────────────────────
// Funções auxiliares
// ─────────────────────────────────────────────

function carregarChavePrivada() {
  const chave = process.env.SOLANA_PRIVATE_KEY;
  if (!chave) {
    console.error("\n❌ ERRO: Variável de ambiente SOLANA_PRIVATE_KEY não encontrada.");
    console.error("   Cria um ficheiro .env com base no .env.example e preenche a tua chave privada.\n");
    process.exit(1);
  }
  return chave;
}

/**
 * Calcula o custo da Merkle Tree em lamports.
 * Fórmula baseada na documentação do Bubblegum.
 */
async function calcularCustoArvore(connection) {
  const { maxDepth, maxBufferSize, canopyDepth } = TREE_CONFIG;

  // Tamanho do account da ConcurrentMerkleTree
  // Fórmula: 8 (discriminator) + 32 (authority) + 32 (creation_slot) +
  //          max_buffer_size * (32 + 8) + 2^(max_depth+1) * 32 +
  //          2^canopy_depth * 32 (canopy nodes)
  const headerBytes = 8 + 32 + 32;
  const changeLogBytes = maxBufferSize * (32 * (maxDepth + 1) + 8 + 4);
  const rightMostPathBytes = 32 * (maxDepth + 1) + 8 + 4;
  const rootBytes = 32;
  const canopyBytes = Math.max((Math.pow(2, canopyDepth + 1) - 2) * 32, 0);

  const treeSize =
    headerBytes +
    changeLogBytes +
    rightMostPathBytes +
    rootBytes +
    canopyBytes;

  // Custo de rent-exemption
  const rentPerByte = await connection.getMinimumBalanceForRentExemption(treeSize);

  return {
    treeSize,
    rentLamports: rentPerByte,
    rentSol: rentPerByte / LAMPORTS_PER_SOL,
  };
}

function formatarSOL(lamports) {
  return (lamports / LAMPORTS_PER_SOL).toFixed(6);
}

// ─────────────────────────────────────────────
// Script principal
// ─────────────────────────────────────────────

async function criarMerkleTree() {
  console.log("\n╔══════════════════════════════════════════════════════════╗");
  console.log("║       REBORNFENIX — Criar Merkle Tree (Passo 2/3)       ║");
  console.log("╚══════════════════════════════════════════════════════════╝\n");

  // Verificar se a coleção foi criada
  const collectionFile = join(__dirname, "collection_address.json");
  if (!existsSync(collectionFile)) {
    console.error("❌ Ficheiro collection_address.json não encontrado!");
    console.error("   Corre primeiro o passo 1: node deploy_collection.js\n");
    process.exit(1);
  }
  const { collectionMint, network: collectionNetwork } = JSON.parse(
    readFileSync(collectionFile, "utf8")
  );
  console.log(`✅ Coleção encontrada: ${collectionMint}`);

  if (collectionNetwork !== NETWORK) {
    console.warn(`\n⚠️  AVISO: A coleção foi criada em "${collectionNetwork}" mas estás a usar "${NETWORK}".`);
    console.warn("   Certifica-te que SOLANA_NETWORK está correcto.\n");
  }

  // Verificar se a árvore já foi criada
  const treeFile = join(__dirname, "tree_address.json");
  if (existsSync(treeFile)) {
    const existing = JSON.parse(readFileSync(treeFile, "utf8"));
    console.log("\n⚠️  A Merkle Tree já foi criada anteriormente!");
    console.log(`   Endereço: ${existing.treeAddress}`);
    console.log(`   Rede: ${existing.network}`);
    console.log("\n   Se queres criar uma nova árvore, apaga tree_address.json.");
    console.log("   Se queres continuar para o minting, corre: node mint_batch.js\n");
    return;
  }

  // Carregar chave privada
  console.log("🔐 A carregar carteira...");
  const privateKeyBase58 = carregarChavePrivada();

  // Inicializar conexão Web3.js para calcular custos
  const rpcUrl = RPC_URLS[NETWORK];
  if (!rpcUrl) {
    console.error(`❌ Rede inválida: "${NETWORK}"`);
    process.exit(1);
  }
  const connection = new Connection(rpcUrl, "confirmed");

  // Inicializar UMI
  console.log(`🌐 A ligar à rede Solana: ${NETWORK}`);
  const umi = createUmi(rpcUrl).use(mplBubblegum());

  // Criar signer
  let keypair;
  try {
    const privateKeyBytes = base58.deserialize(privateKeyBase58)[0];
    keypair = umi.eddsa.createKeypairFromSecretKey(privateKeyBytes);
  } catch (err) {
    console.error("\n❌ Formato de chave privada inválido:");
    console.error(`   ${err.message}\n`);
    process.exit(1);
  }

  const signer = createSignerFromKeypair(umi, keypair);
  umi.use(signerIdentity(signer));

  const walletAddress = keypair.publicKey;
  console.log(`   Carteira: ${walletAddress}`);

  // Verificar saldo
  const balance = await connection.getBalance(new PublicKey(walletAddress));
  const solBalance = balance / LAMPORTS_PER_SOL;
  console.log(`   Saldo: ${solBalance.toFixed(6)} SOL`);

  // Calcular e mostrar custos ANTES de criar
  console.log("\n💰 A calcular custos...");
  const { treeSize, rentLamports, rentSol } = await calcularCustoArvore(connection);

  const txFeeEstimate = 0.000005; // ~5000 lamports por transacção
  const totalEstimado = rentSol + txFeeEstimate;

  console.log("\n┌─────────────────────────────────────────────────────────┐");
  console.log("│                  DETALHES DA MERKLE TREE                │");
  console.log("├─────────────────────────────────────────────────────────┤");
  console.log(`│  Profundidade máxima (maxDepth)   : ${TREE_CONFIG.maxDepth}               │`);
  console.log(`│  Capacidade máxima               : ${Math.pow(2, TREE_CONFIG.maxDepth).toLocaleString()} NFTs  │`);
  console.log(`│  NFTs a cunhar                   : ${TOTAL_NFTS.toLocaleString()}            │`);
  console.log(`│  Buffer size                     : ${TREE_CONFIG.maxBufferSize}                   │`);
  console.log(`│  Canopy depth                    : ${TREE_CONFIG.canopyDepth}                   │`);
  console.log(`│  Tamanho do account              : ${(treeSize / 1024).toFixed(1)} KB             │`);
  console.log("├─────────────────────────────────────────────────────────┤");
  console.log(`│  Custo de rent-exemption         : ${rentSol.toFixed(6)} SOL       │`);
  console.log(`│  Custo de transacção (estimado)  : ${txFeeEstimate.toFixed(6)} SOL       │`);
  console.log(`│  CUSTO TOTAL ESTIMADO            : ~${totalEstimado.toFixed(6)} SOL  │`);
  if (NETWORK === "mainnet-beta") {
    const solPrice = 150; // preço estimado em USD — actualiza conforme necessário
    console.log(`│  (aproximadamente $${(totalEstimado * solPrice).toFixed(2)} USD a $${solPrice}/SOL)           │`);
  }
  console.log("└─────────────────────────────────────────────────────────┘");

  if (solBalance < totalEstimado * 1.1) {
    console.error(`\n❌ Saldo insuficiente!`);
    console.error(`   Precisas de pelo menos ${(totalEstimado * 1.1).toFixed(6)} SOL.`);
    console.error(`   Saldo actual: ${solBalance.toFixed(6)} SOL`);
    if (NETWORK === "devnet") {
      console.error("   Obtém SOL de teste em: https://faucet.solana.com");
    }
    process.exit(1);
  }

  // Confirmação em mainnet
  if (NETWORK === "mainnet-beta") {
    console.log("\n⚠️  ATENÇÃO: Estás prestes a criar a Merkle Tree na MAINNET!");
    console.log(`   Custo: ~${totalEstimado.toFixed(6)} SOL`);
    console.log("   Se não tens a certeza, usa SOLANA_NETWORK=devnet primeiro.\n");
    // Em produção podes adicionar um prompt interactivo aqui
    // Para automação, continuamos directamente
  }

  // Criar a Merkle Tree
  console.log("\n🌳 A criar a Merkle Tree na blockchain...");
  console.log("   (Isto pode demorar 30-60 segundos)");

  const merkleTree = generateSigner(umi);

  let signature;
  try {
    const { signature: sig } = await createTree(umi, {
      merkleTree,
      maxDepth: TREE_CONFIG.maxDepth,
      maxBufferSize: TREE_CONFIG.maxBufferSize,
      canopyDepth: TREE_CONFIG.canopyDepth,
    }).sendAndConfirm(umi, {
      confirm: { commitment: "finalized" },
      send: { skipPreflight: false },
    });
    signature = sig;
  } catch (err) {
    console.error("\n❌ ERRO ao criar a Merkle Tree:");
    console.error(`   ${err.message}`);
    if (err.message?.includes("insufficient funds")) {
      console.error("\n   Saldo insuficiente. Adiciona mais SOL à tua carteira.");
    } else if (err.message?.includes("custom program error: 0x1")) {
      console.error("\n   Parâmetros inválidos para a árvore.");
    }
    process.exit(1);
  }

  const treeAddress = merkleTree.publicKey;
  const txSignature = base58.serialize(signature);

  console.log("\n✅ MERKLE TREE CRIADA COM SUCESSO!\n");
  console.log(`   Endereço da Árvore : ${treeAddress}`);
  console.log(`   Transacção         : ${txSignature}`);

  const explorerBase =
    NETWORK === "mainnet-beta"
      ? "https://explorer.solana.com"
      : "https://explorer.solana.com/?cluster=devnet";
  console.log(`   Explorer           : ${explorerBase}/address/${treeAddress}`);

  // Guardar endereço da árvore
  const result = {
    treeAddress: treeAddress,
    collectionMint,
    network: NETWORK,
    transaction: txSignature,
    config: TREE_CONFIG,
    maxNFTs: Math.pow(2, TREE_CONFIG.maxDepth),
    createdAt: new Date().toISOString(),
  };

  writeFileSync(treeFile, JSON.stringify(result, null, 2));
  console.log(`\n   💾 Endereço guardado em: ${treeFile}`);

  console.log("\n📝 Próximos passos:");
  console.log(`   1. Adiciona ao teu .env:`);
  console.log(`      TREE_ADDRESS=${treeAddress}`);
  console.log("   2. Gera os metadata: cd ../metadata && python metadata_generator.py");
  console.log("   3. Faz o minting: node mint_batch.js\n");
}

criarMerkleTree().catch((err) => {
  console.error("\n💥 Erro inesperado:", err.message);
  console.error(err.stack);
  process.exit(1);
});
