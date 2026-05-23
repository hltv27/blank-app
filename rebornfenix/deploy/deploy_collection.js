/**
 * REBORNFENIX — deploy_collection.js
 * Cria o NFT de coleção pai no Solana usando Metaplex Token Metadata.
 * Este é o passo 1 de 3. Corre ANTES de create_merkle_tree.js.
 *
 * Uso:
 *   SOLANA_NETWORK=devnet node deploy_collection.js       # teste
 *   SOLANA_NETWORK=mainnet-beta node deploy_collection.js # produção
 */

import { createUmi } from "@metaplex-foundation/umi-bundle-defaults";
import {
  createNft,
  mplTokenMetadata,
} from "@metaplex-foundation/mpl-token-metadata";
import {
  createSignerFromKeypair,
  signerIdentity,
  generateSigner,
  percentAmount,
  sol,
} from "@metaplex-foundation/umi";
import { base58 } from "@metaplex-foundation/umi/serializers";
import { readFileSync, writeFileSync, existsSync } from "fs";
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

const COLLECTION_CONFIG = {
  name: "REBORNFENIX",
  symbol: "RBFX",
  description:
    "22,222 Viking warriors forged in the fires of Ragnarök — fathers, fighters, and survivors who stared into the abyss and refused to break. Each warrior carries the ancient power of Elder Futhark runes. Where Norse cosmology meets the unbreakable spirit of those who trade darkness for dawn.",
  // Substitui este URL pelo teu CID do IPFS depois de fazer upload da imagem
  // Vê ipfs_upload_guide.md para instruções detalhadas
  image: process.env.COLLECTION_IMAGE_URI || "ipfs://QmPLACEHOLDER_SOBE_O_IPFS_CID_DA_TUA_IMAGEM",
  royalties: 500, // 5% em basis points (500 = 5%)
  sellerFeeBasisPoints: 500,
  creators: [
    // O endereço do criador é preenchido automaticamente com a chave pública da tua carteira
    // Podes adicionar mais criadores aqui se quiseres dividir royalties
  ],
};

// ─────────────────────────────────────────────
// Funções auxiliares
// ─────────────────────────────────────────────

function carregarChavePrivada() {
  const chave = process.env.SOLANA_PRIVATE_KEY;
  if (!chave) {
    console.error("\n❌ ERRO: Variável de ambiente SOLANA_PRIVATE_KEY não encontrada.");
    console.error("   Cria um ficheiro .env com base no .env.example e preenche a tua chave privada.");
    console.error("   Nunca partilhes ou commites a tua chave privada!\n");
    process.exit(1);
  }
  return chave;
}

function construirMetadataUri() {
  // O metadata da coleção pai é um JSON simples — aqui usamos um data URI inline
  // Em produção, faz upload deste JSON para IPFS também e usa o URI real
  const metadata = {
    name: COLLECTION_CONFIG.name,
    symbol: COLLECTION_CONFIG.symbol,
    description: COLLECTION_CONFIG.description,
    image: COLLECTION_CONFIG.image,
    external_url: "https://rebornfenix.io",
    attributes: [],
    properties: {
      files: [
        {
          uri: COLLECTION_CONFIG.image,
          type: "image/png",
        },
      ],
      category: "image",
    },
  };

  // Guarda o metadata localmente para referência
  const metadataPath = join(__dirname, "collection_metadata.json");
  writeFileSync(metadataPath, JSON.stringify(metadata, null, 2));
  console.log(`   📄 Metadata da coleção guardado em: ${metadataPath}`);
  console.log(`   ⚠️  IMPORTANTE: Faz upload deste JSON para IPFS e actualiza COLLECTION_METADATA_URI`);

  // Se tiver URI de metadata definida, usa essa; senão avisa
  const uri = process.env.COLLECTION_METADATA_URI;
  if (!uri) {
    console.warn("\n   ⚠️  COLLECTION_METADATA_URI não definida. Usando URI de placeholder.");
    console.warn("   Segue o ipfs_upload_guide.md para fazer upload da imagem e do metadata.\n");
    return "ipfs://QmPLACEHOLDER_METADATA_JSON_CID";
  }
  return uri;
}

// ─────────────────────────────────────────────
// Script principal
// ─────────────────────────────────────────────

async function deployColecao() {
  console.log("\n╔══════════════════════════════════════════════════════════╗");
  console.log("║          REBORNFENIX — Deploy da Coleção (Passo 1/3)    ║");
  console.log("╚══════════════════════════════════════════════════════════╝\n");

  // Verificar se já foi feito o deploy
  const addressFile = join(__dirname, "collection_address.json");
  if (existsSync(addressFile)) {
    const existing = JSON.parse(readFileSync(addressFile, "utf8"));
    console.log("⚠️  A coleção já foi criada anteriormente!");
    console.log(`   Endereço: ${existing.collectionMint}`);
    console.log(`   Rede: ${existing.network}`);
    console.log("\n   Se queres criar uma nova coleção, apaga o ficheiro collection_address.json.");
    console.log("   Se queres continuar para o passo seguinte, corre: node create_merkle_tree.js\n");
    return;
  }

  // Carregar e validar chave privada
  console.log("🔐 A carregar carteira...");
  const privateKeyBase58 = carregarChavePrivada();

  // Inicializar UMI
  console.log(`🌐 A ligar à rede Solana: ${NETWORK}`);
  const rpcUrl = RPC_URLS[NETWORK];
  if (!rpcUrl) {
    console.error(`❌ Rede inválida: "${NETWORK}". Usa "devnet" ou "mainnet-beta".`);
    process.exit(1);
  }

  const umi = createUmi(rpcUrl).use(mplTokenMetadata());

  // Criar signer a partir da chave privada
  let keypair;
  try {
    const privateKeyBytes = base58.deserialize(privateKeyBase58)[0];
    keypair = umi.eddsa.createKeypairFromSecretKey(privateKeyBytes);
  } catch (err) {
    console.error("\n❌ ERRO: A chave privada tem formato inválido.");
    console.error("   Certifica-te que está em formato base58 (começa com números e letras).");
    console.error(`   Detalhe: ${err.message}\n`);
    process.exit(1);
  }

  const signer = createSignerFromKeypair(umi, keypair);
  umi.use(signerIdentity(signer));

  const walletAddress = keypair.publicKey;
  console.log(`   Carteira: ${walletAddress}`);

  // Verificar saldo
  try {
    const balance = await umi.rpc.getBalance(walletAddress);
    const solBalance = Number(balance.basisPoints) / 1e9;
    console.log(`   Saldo: ${solBalance.toFixed(4)} SOL`);

    const minRequired = NETWORK === "mainnet-beta" ? 0.02 : 0.01;
    if (solBalance < minRequired) {
      console.error(`\n❌ Saldo insuficiente! Precisas de pelo menos ${minRequired} SOL.`);
      if (NETWORK === "devnet") {
        console.error("   Para devnet, obtém SOL de teste em: https://faucet.solana.com");
      }
      process.exit(1);
    }
  } catch (err) {
    console.warn(`\n⚠️  Não foi possível verificar o saldo: ${err.message}`);
    console.warn("   A continuar na mesma...\n");
  }

  // Preparar metadata URI
  console.log("\n📋 A preparar metadata da coleção...");
  const metadataUri = construirMetadataUri();
  console.log(`   URI: ${metadataUri}`);

  // Configurar criadores com a carteira actual
  const creators = [
    {
      address: walletAddress,
      verified: true,
      share: 100,
    },
  ];

  // Criar o NFT de coleção
  console.log("\n🚀 A criar NFT de coleção na blockchain...");
  console.log(`   Nome: ${COLLECTION_CONFIG.name}`);
  console.log(`   Símbolo: ${COLLECTION_CONFIG.symbol}`);
  console.log(`   Royalties: ${COLLECTION_CONFIG.royalties / 100}%`);

  const collectionMint = generateSigner(umi);

  let signature;
  try {
    const { signature: sig } = await createNft(umi, {
      mint: collectionMint,
      name: COLLECTION_CONFIG.name,
      symbol: COLLECTION_CONFIG.symbol,
      uri: metadataUri,
      sellerFeeBasisPoints: percentAmount(
        COLLECTION_CONFIG.royalties / 100,
        2
      ),
      creators,
      isCollection: true,
    }).sendAndConfirm(umi, {
      confirm: { commitment: "finalized" },
      send: { skipPreflight: false },
    });
    signature = sig;
  } catch (err) {
    console.error("\n❌ ERRO ao criar a coleção na blockchain:");
    console.error(`   ${err.message}`);
    if (err.message?.includes("insufficient funds")) {
      console.error("\n   A tua carteira não tem SOL suficiente para pagar as taxas.");
    } else if (err.message?.includes("blockhash")) {
      console.error("\n   Problema de conectividade com o RPC. Tenta novamente.");
    }
    process.exit(1);
  }

  const collectionMintAddress = collectionMint.publicKey;
  const txSignature = base58.serialize(signature);

  console.log("\n✅ COLEÇÃO CRIADA COM SUCESSO!\n");
  console.log(`   Mint da Coleção : ${collectionMintAddress}`);
  console.log(`   Transacção      : ${txSignature}`);

  const explorerBase =
    NETWORK === "mainnet-beta"
      ? "https://explorer.solana.com"
      : "https://explorer.solana.com/?cluster=devnet";
  console.log(`   Explorer        : ${explorerBase}/address/${collectionMintAddress}`);

  // Guardar endereço da coleção
  const result = {
    collectionMint: collectionMintAddress,
    collectionName: COLLECTION_CONFIG.name,
    symbol: COLLECTION_CONFIG.symbol,
    network: NETWORK,
    transaction: txSignature,
    createdAt: new Date().toISOString(),
    metadataUri,
  };

  writeFileSync(addressFile, JSON.stringify(result, null, 2));
  console.log(`\n   💾 Endereço guardado em: ${addressFile}`);

  // Actualizar .env com o endereço
  console.log("\n📝 Próximos passos:");
  console.log(`   1. Adiciona este endereço ao teu .env:`);
  console.log(`      COLLECTION_ADDRESS=${collectionMintAddress}`);
  console.log(`   2. Corre o passo seguinte: node create_merkle_tree.js`);
  console.log(`   3. Depois de ter a imagem no IPFS, actualiza o metadata da coleção\n`);
}

deployColecao().catch((err) => {
  console.error("\n💥 Erro inesperado:", err.message);
  console.error(err.stack);
  process.exit(1);
});
