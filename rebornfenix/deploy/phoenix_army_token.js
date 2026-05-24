/**
 * REBORNFENIX — phoenix_army_token.js
 * Deploy do token SPL fungível do Exército da Fénix (Phoenix Army).
 *
 * O que este script faz:
 *   1. Cria um token SPL com 0 casas decimais (tokens inteiros — necessário para o sistema de postos)
 *   2. Cunha exactamente 522,222 tokens para a carteira criadora
 *   3. REVOGA a mint authority — ninguém pode cunhar mais tokens, NUNCA
 *   4. Adiciona metadata on-chain (nome, símbolo, imagem, descrição)
 *   5. Guarda o endereço do mint em army_token_address.json para referência futura
 *
 * PORQUÊ REVOGAR A MINT AUTHORITY?
 *   Revogar a mint authority é a PROVA CRIPTOGRÁFICA do hard cap.
 *   Depois da revogação, nem o fundador, nem ninguém com acesso à carteira
 *   pode criar mais tokens. O contrato inteligente da Solana recusa qualquer
 *   tentativa de mint — não há excepções, não há overrides, não há "se eu quiser".
 *   522,222 tokens. Para sempre. Verificável por qualquer pessoa no Solana Explorer.
 *
 * Sistema de postos (11 ranks):
 *   Recruta (1) → Soldado (2-10) → Cabo (11-50) → Sargento (51-100)
 *   → Tenente (101-500) → Capitão (501-1000) → Major (1001-5000)
 *   → Coronel (5001-10000) → General (10001-50000)
 *   → Marechal (50001-100000) → Comandante Supremo (100001+)
 *
 * Uso:
 *   SOLANA_NETWORK=devnet node phoenix_army_token.js       # teste
 *   SOLANA_NETWORK=mainnet-beta node phoenix_army_token.js # produção
 *
 * Pré-requisitos:
 *   - SOLANA_PRIVATE_KEY no .env (formato base58)
 *   - Saldo SOL suficiente (~0.05 SOL para devnet, ~0.02 SOL para mainnet)
 *   - node >= 18, dependências instaladas (npm install)
 */

import { createUmi } from "@metaplex-foundation/umi-bundle-defaults";
import {
  createFungible,
  mplTokenMetadata,
} from "@metaplex-foundation/mpl-token-metadata";
import {
  createSignerFromKeypair,
  signerIdentity,
  generateSigner,
  percentAmount,
} from "@metaplex-foundation/umi";
import { base58 } from "@metaplex-foundation/umi/serializers";
import {
  mintV1,
  TokenStandard,
} from "@metaplex-foundation/mpl-token-metadata";
import { readFileSync, writeFileSync, existsSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import "dotenv/config";

// ─────────────────────────────────────────────
// Configuração do Token
// ─────────────────────────────────────────────
const __dirname = dirname(fileURLToPath(import.meta.url));

const NETWORK = process.env.SOLANA_NETWORK || "devnet";
const RPC_URLS = {
  devnet: "https://api.devnet.solana.com",
  "mainnet-beta": "https://api.mainnet-beta.solana.com",
};

const TOKEN_CONFIG = {
  name: "REBORNFENIX Army",
  symbol: "RBFXA",
  description:
    "O Exército da Fénix — 522,222 tokens fungíveis do ecossistema REBORNFENIX. " +
    "Cada token é um posto. Acumula tokens para avançar nos 11 postos militares. " +
    "Emissão fechada para sempre: a mint authority foi revogada após criação. " +
    "O número 22 corre em todo o projecto: 22 Founding Warriors · 22.222 Legion · 522.222 Phoenix Army. | " +
    "The Phoenix Army — 522,222 fungible tokens of the REBORNFENIX ecosystem. " +
    "Accumulate tokens to advance through 11 military ranks. Hard cap forever.",
  image:
    process.env.ARMY_TOKEN_IMAGE_URI ||
    "ipfs://QmPLACEHOLDER_PHOENIX_ARMY_TOKEN_IMAGE",
  decimals: 0, // Tokens inteiros — necessário para o sistema de postos (não podes ter 0.5 de um posto)
  totalSupply: 522222, // 522.222 — o número 22 corre em todo o projecto
  royalties: 0, // Tokens fungíveis não têm royalties de secondary sales
};

// ─────────────────────────────────────────────
// Funções auxiliares
// ─────────────────────────────────────────────

function carregarChavePrivada() {
  const chave = process.env.SOLANA_PRIVATE_KEY;
  if (!chave) {
    console.error(
      "\nERRO: Variável de ambiente SOLANA_PRIVATE_KEY não encontrada."
    );
    console.error(
      "   Cria um ficheiro .env com base no .env.example e preenche a tua chave privada."
    );
    console.error("   Nunca partilhes ou commites a tua chave privada!\n");
    process.exit(1);
  }
  return chave;
}

function construirMetadataUri() {
  // Metadata off-chain do token (Metaplex Token Metadata standard)
  const metadata = {
    name: TOKEN_CONFIG.name,
    symbol: TOKEN_CONFIG.symbol,
    description: TOKEN_CONFIG.description,
    image: TOKEN_CONFIG.image,
    external_url: "https://rebornfenix.io/army",
    attributes: [
      { trait_type: "Tier",          value: "Phoenix Army" },
      { trait_type: "Token Type",    value: "Fungible SPL" },
      { trait_type: "Total Supply",  value: "522,222" },
      { trait_type: "Decimals",      value: "0" },
      { trait_type: "Hard Cap",      value: "Yes — Mint Authority Revoked" },
      { trait_type: "Autism Donation", value: "20% of revenue" },
      { trait_type: "Ranks",         value: "11 Military Ranks" },
      { trait_type: "Project",       value: "REBORNFENIX" },
    ],
    properties: {
      files: [{ uri: TOKEN_CONFIG.image, type: "image/png" }],
      category: "image",
    },
    extensions: {
      website: "https://rebornfenix.io",
      donation_proof: "https://rebornfenix.io/compromisos",
      hard_cap_proof:
        "Mint authority revoked on-chain. Verify at https://explorer.solana.com",
      ranks: [
        { rank: "Recruta",            min: 1,      max: 1      },
        { rank: "Soldado",            min: 2,      max: 10     },
        { rank: "Cabo",               min: 11,     max: 50     },
        { rank: "Sargento",           min: 51,     max: 100    },
        { rank: "Tenente",            min: 101,    max: 500    },
        { rank: "Capitão",            min: 501,    max: 1000   },
        { rank: "Major",              min: 1001,   max: 5000   },
        { rank: "Coronel",            min: 5001,   max: 10000  },
        { rank: "General",            min: 10001,  max: 50000  },
        { rank: "Marechal",           min: 50001,  max: 100000 },
        { rank: "Comandante Supremo", min: 100001, max: null   },
      ],
    },
  };

  // Guarda metadata localmente
  const metadataPath = join(__dirname, "army_token_metadata.json");
  writeFileSync(metadataPath, JSON.stringify(metadata, null, 2));
  console.log(`   Metadata guardado em: ${metadataPath}`);
  console.log(
    `   IMPORTANTE: Faz upload deste JSON para IPFS e define ARMY_TOKEN_METADATA_URI no .env`
  );

  const uri = process.env.ARMY_TOKEN_METADATA_URI;
  if (!uri) {
    console.warn(
      "\n   AVISO: ARMY_TOKEN_METADATA_URI não definida. Usando URI de placeholder."
    );
    console.warn(
      "   Segue o ipfs_upload_guide.md para fazer upload do metadata.\n"
    );
    return "ipfs://QmPLACEHOLDER_ARMY_TOKEN_METADATA_JSON_CID";
  }
  return uri;
}

// ─────────────────────────────────────────────
// Script principal
// ─────────────────────────────────────────────

async function deployPhoenixArmyToken() {
  console.log(
    "\n╔══════════════════════════════════════════════════════════════╗"
  );
  console.log(
    "║       REBORNFENIX — Deploy do Token Phoenix Army (RBFXA)    ║"
  );
  console.log(
    "╚══════════════════════════════════════════════════════════════╝\n"
  );

  console.log("  Token:       REBORNFENIX Army (RBFXA)");
  console.log("  Supply:      522,222 tokens (hard cap para sempre)");
  console.log("  Decimais:    0 (tokens inteiros — sistema de postos)");
  console.log(
    "  Assinatura:  22 · 22.222 · 522.222 — o 22 corre em todo o projecto"
  );
  console.log("  Doação:      20% da receita para investigação do autismo\n");

  // Verificar se já foi feito o deploy
  const addressFile = join(__dirname, "army_token_address.json");
  if (existsSync(addressFile)) {
    const existing = JSON.parse(readFileSync(addressFile, "utf8"));
    console.log("AVISO: O token Phoenix Army já foi criado anteriormente!");
    console.log(`   Mint address: ${existing.mintAddress}`);
    console.log(`   Rede: ${existing.network}`);
    console.log(`   Data: ${existing.createdAt}`);
    console.log(
      "\n   Se queres criar um novo token, apaga o ficheiro army_token_address.json."
    );
    console.log(
      "   ATENÇÃO: Isso criaria um segundo token — o hard cap do primeiro mantém-se.\n"
    );
    return;
  }

  // Validar rede
  const rpcUrl = RPC_URLS[NETWORK];
  if (!rpcUrl) {
    console.error(
      `\nERRO: Rede inválida "${NETWORK}". Usa "devnet" ou "mainnet-beta".`
    );
    process.exit(1);
  }

  // Carregar chave privada
  console.log("A carregar carteira...");
  const privateKeyBase58 = carregarChavePrivada();

  // Inicializar UMI
  console.log(`A ligar à rede Solana: ${NETWORK} (${rpcUrl})`);
  const umi = createUmi(rpcUrl).use(mplTokenMetadata());

  // Criar signer
  let keypair;
  try {
    const privateKeyBytes = base58.deserialize(privateKeyBase58)[0];
    keypair = umi.eddsa.createKeypairFromSecretKey(privateKeyBytes);
  } catch (err) {
    console.error("\nERRO: A chave privada tem formato inválido.");
    console.error(
      "   Certifica-te que está em formato base58 (começa com números e letras)."
    );
    console.error(`   Detalhe: ${err.message}\n`);
    process.exit(1);
  }

  const signer = createSignerFromKeypair(umi, keypair);
  umi.use(signerIdentity(signer));

  const walletAddress = keypair.publicKey;
  console.log(`   Carteira: ${walletAddress}`);

  // Verificar saldo SOL
  try {
    const balance = await umi.rpc.getBalance(walletAddress);
    const solBalance = Number(balance.basisPoints) / 1e9;
    console.log(`   Saldo: ${solBalance.toFixed(4)} SOL`);

    const minRequired = NETWORK === "mainnet-beta" ? 0.02 : 0.01;
    if (solBalance < minRequired) {
      console.error(
        `\nERRO: Saldo insuficiente. Precisas de pelo menos ${minRequired} SOL.`
      );
      if (NETWORK === "devnet") {
        console.error(
          "   Para devnet, obtém SOL de teste em: https://faucet.solana.com"
        );
      }
      process.exit(1);
    }
  } catch (err) {
    console.warn(`\nAVISO: Não foi possível verificar o saldo: ${err.message}`);
    console.warn("   A continuar na mesma...\n");
  }

  // Preparar metadata URI
  console.log("\nA preparar metadata do token...");
  const metadataUri = construirMetadataUri();
  console.log(`   URI: ${metadataUri}`);

  // Passo 1: Criar o token fungível com metadata on-chain
  console.log("\n─────────────────────────────────────────");
  console.log("PASSO 1/3: Criar token fungível RBFXA");
  console.log("─────────────────────────────────────────");
  console.log(`   Nome:    ${TOKEN_CONFIG.name}`);
  console.log(`   Símbolo: ${TOKEN_CONFIG.symbol}`);
  console.log(`   Supply:  ${TOKEN_CONFIG.totalSupply.toLocaleString()} tokens`);
  console.log(`   Decimais: ${TOKEN_CONFIG.decimals} (tokens inteiros)`);
  console.log(
    "   Nota: 0 casas decimais é fundamental — não podes ter meio posto militar.\n"
  );

  const mintSigner = generateSigner(umi);

  let createSignature;
  try {
    const { signature } = await createFungible(umi, {
      mint: mintSigner,
      name: TOKEN_CONFIG.name,
      symbol: TOKEN_CONFIG.symbol,
      uri: metadataUri,
      sellerFeeBasisPoints: percentAmount(0, 2), // 0% royalties para token fungível
      decimals: TOKEN_CONFIG.decimals,
      isMutable: true, // metadata pode ser actualizada (para actualizar image URI após IPFS upload)
    }).sendAndConfirm(umi, {
      confirm: { commitment: "finalized" },
      send: { skipPreflight: false },
    });
    createSignature = signature;
  } catch (err) {
    console.error("\nERRO ao criar o token:");
    console.error(`   ${err.message}`);
    if (err.message?.includes("insufficient funds")) {
      console.error(
        "\n   A tua carteira não tem SOL suficiente para pagar as taxas de criação."
      );
    }
    process.exit(1);
  }

  const mintAddress = mintSigner.publicKey;
  const createTxSig = base58.serialize(createSignature);

  console.log("   Token criado com sucesso!");
  console.log(`   Mint address: ${mintAddress}`);
  console.log(`   Transacção: ${createTxSig}`);

  // Passo 2: Cunhar exactamente 522,222 tokens para a carteira criadora
  console.log("\n─────────────────────────────────────────");
  console.log("PASSO 2/3: Cunhar 522,222 tokens (supply completo)");
  console.log("─────────────────────────────────────────");
  console.log(
    "   Todos os 522,222 tokens são criados de uma só vez para a carteira do criador."
  );
  console.log(
    "   A partir daqui, o criador distribui os tokens via website de venda."
  );
  console.log(
    "   IMPORTANTE: Depois da revogação (Passo 3), NÃO será possível criar mais.\n"
  );

  let mintSignature;
  try {
    const { signature } = await mintV1(umi, {
      mint: mintAddress,
      tokenStandard: TokenStandard.Fungible,
      amount: BigInt(TOKEN_CONFIG.totalSupply),
    }).sendAndConfirm(umi, {
      confirm: { commitment: "finalized" },
      send: { skipPreflight: false },
    });
    mintSignature = signature;
  } catch (err) {
    console.error(`\nERRO ao cunhar os tokens:`);
    console.error(`   ${err.message}`);
    console.error(
      "\n   ATENÇÃO: O token foi criado (Passo 1 completo) mas o mint falhou."
    );
    console.error(
      `   Mint address: ${mintAddress}`
    );
    console.error(
      "   Guarda este endereço e tenta cunhar manualmente via Solana CLI ou Phantom."
    );
    console.error(
      "   NÃO revogues a mint authority antes de confirmares que os 522,222 tokens foram cunhados."
    );
    process.exit(1);
  }

  const mintTxSig = base58.serialize(mintSignature);
  console.log("   522,222 tokens cunhados com sucesso!");
  console.log(`   Transacção: ${mintTxSig}`);
  console.log(`   Tokens na carteira: ${TOKEN_CONFIG.totalSupply.toLocaleString()} RBFXA`);

  // Passo 3: Revogar a mint authority — PROVA CRIPTOGRÁFICA DO HARD CAP
  console.log("\n─────────────────────────────────────────");
  console.log("PASSO 3/3: REVOGAR MINT AUTHORITY (hard cap definitivo)");
  console.log("─────────────────────────────────────────");
  console.log("");
  console.log("  *** ESTE E O PASSO MAIS IMPORTANTE DE TODO O PROJECTO ***");
  console.log("");
  console.log("  Ao revogar a mint authority, estamos a fazer uma promessa");
  console.log("  que NINGUEM pode quebrar — nem o fundador, nem um hacker,");
  console.log("  nem um governo, nem qualquer pressão externa:");
  console.log("");
  console.log("  522,222 tokens. Para sempre. Sem excepções.");
  console.log("");
  console.log("  Esta revogação fica gravada na blockchain da Solana");
  console.log("  e é verificável por qualquer pessoa, em qualquer momento,");
  console.log("  em https://explorer.solana.com");
  console.log("");
  console.log("  HARD CAP PROVADO ON-CHAIN. NAO HA MAIS TOKENS. NUNCA.");
  console.log("");

  let revokeSignature;
  try {
    // Para revogar a mint authority num token Metaplex Fungible,
    // usamos setAuthority do Token Program directamente via umi
    const { setAuthority } = await import("@solana/spl-token");
    const { Connection, PublicKey, Keypair } = await import("@solana/web3.js");

    const connection = new Connection(rpcUrl, "finalized");

    // Reconstruir o keypair no formato @solana/web3.js
    const privateKeyBytes = base58.deserialize(privateKeyBase58)[0];
    const web3Keypair = Keypair.fromSecretKey(privateKeyBytes);

    const mintPubkey = new PublicKey(mintAddress.toString());

    const revokeTx = await setAuthority(
      connection,
      web3Keypair,        // payer
      mintPubkey,         // mint account
      web3Keypair,        // current authority
      0,                  // AuthorityType.MintTokens = 0
      null,               // null = revoke (no new authority)
      [],                 // multi-signers
      { commitment: "finalized" }
    );

    revokeSignature = revokeTx;
  } catch (err) {
    console.error("\nERRO ao revogar a mint authority:");
    console.error(`   ${err.message}`);
    console.error(
      "\n   CRITICO: Os tokens foram cunhados mas a authority NAO foi revogada."
    );
    console.error(
      "   O hard cap NAO esta provado on-chain ate completares este passo."
    );
    console.error(`   Mint address: ${mintAddress}`);
    console.error(
      "   Revoga manualmente com: spl-token authorize <MINT_ADDRESS> mint --disable"
    );
    console.error("   Ou usa o Solana CLI / Phantom Wallet para revogar.");

    // Guardar o endereço mesmo assim para não perder o trabalho feito
    const partialResult = {
      mintAddress: mintAddress.toString(),
      symbol: TOKEN_CONFIG.symbol,
      name: TOKEN_CONFIG.name,
      totalSupply: TOKEN_CONFIG.totalSupply,
      decimals: TOKEN_CONFIG.decimals,
      network: NETWORK,
      createTransaction: createTxSig,
      mintTransaction: mintTxSig,
      revokeTransaction: null,
      mintAuthorityRevoked: false,
      WARNING:
        "MINT AUTHORITY NOT REVOKED — HARD CAP NOT PROVEN. Revoke manually before distributing tokens.",
      createdAt: new Date().toISOString(),
    };
    writeFileSync(addressFile, JSON.stringify(partialResult, null, 2));
    console.error(`\n   Endereço parcial guardado em: ${addressFile}`);
    process.exit(1);
  }

  console.log("   Mint authority REVOGADA com sucesso!");
  console.log(`   Transacção: ${revokeSignature}`);
  console.log("");
  console.log("   HARD CAP PROVADO ON-CHAIN:");
  console.log("   - 522,222 tokens existem");
  console.log("   - Nao podem ser criados mais");
  console.log("   - Verificavel por qualquer pessoa na blockchain");
  console.log("   - Permanente e irreversivel");
  console.log("");

  // Determinar URL do explorer
  const explorerBase =
    NETWORK === "mainnet-beta"
      ? "https://explorer.solana.com"
      : "https://explorer.solana.com/?cluster=devnet";

  console.log(
    "  *** HARD CAP ESTABELECIDO — 522,222 RBFXA PARA SEMPRE ***"
  );
  console.log("");
  console.log(`   Explorer: ${explorerBase}/address/${mintAddress}`);
  console.log(
    "   Partilha este link como PROVA do hard cap para os teus holders."
  );
  console.log("");

  // Guardar todos os dados do deploy
  const result = {
    mintAddress: mintAddress.toString(),
    symbol: TOKEN_CONFIG.symbol,
    name: TOKEN_CONFIG.name,
    totalSupply: TOKEN_CONFIG.totalSupply,
    decimals: TOKEN_CONFIG.decimals,
    network: NETWORK,
    createTransaction: createTxSig,
    mintTransaction: mintTxSig,
    revokeTransaction: revokeSignature,
    mintAuthorityRevoked: true,
    hardCapProven: true,
    explorerUrl: `${explorerBase}/address/${mintAddress}`,
    metadataUri,
    createdAt: new Date().toISOString(),
    notes: {
      hard_cap: "Mint authority revoked on-chain. 522,222 RBFXA tokens forever.",
      ranks:
        "11 military ranks based on token balance. See candy_machine_config.json for rank thresholds.",
      distribution:
        "Tokens held in creator wallet. Distribute via website sale at 0.10 USDC each.",
      autism_donation:
        "20% of all sale revenue donated to autism research. Proof at https://rebornfenix.io/compromisos",
      numerical_signature:
        "22 · 22.222 · 522.222 — the number 22 runs through the entire REBORNFENIX project.",
    },
  };

  writeFileSync(addressFile, JSON.stringify(result, null, 2));
  console.log(`   Dados do deploy guardados em: ${addressFile}`);

  // Instrucoes pos-deploy
  console.log("\n─────────────────────────────────────────");
  console.log("PROXIMOS PASSOS");
  console.log("─────────────────────────────────────────");
  console.log("");
  console.log("1. Adiciona o mint address ao .env:");
  console.log(`   PHOENIX_ARMY_MINT=${mintAddress}`);
  console.log("");
  console.log("2. Actualiza o candy_machine_config.json com o mint address:");
  console.log(
    `   Procura 'phoenix_army' no config e adiciona "mintAddress": "${mintAddress}"`
  );
  console.log("");
  console.log("3. Faz upload da imagem do token para IPFS:");
  console.log(
    "   Vê ipfs_upload_guide.md para instrucoes detalhadas."
  );
  console.log("   Depois define ARMY_TOKEN_METADATA_URI no .env com o CID.");
  console.log("");
  console.log("4. Actualiza o metadata on-chain com o URI correcto:");
  console.log(
    "   (Usa Metaplex Sugar ou Solana CLI para actualizar o URI do metadata)"
  );
  console.log("");
  console.log("5. Cria a pagina de venda em https://rebornfenix.io/army");
  console.log("   com o endereco do mint para verificacao pelos compradores.");
  console.log("");
  console.log("6. Partilha o Explorer URL como prova do hard cap:");
  console.log(`   ${explorerBase}/address/${mintAddress}`);
  console.log("");
  console.log("7. Publica o primeiro Comprovativo Mensal em:");
  console.log("   https://rebornfenix.io/compromisos");
  console.log("");
  console.log(
    "   PROJECTO REBORNFENIX — 544,466 guerreiros. Um juramento. Sem rendicao."
  );
  console.log(
    "   22 Founding Warriors · 22,222 Legion of Honour · 522,222 Phoenix Army"
  );
  console.log("");
}

deployPhoenixArmyToken().catch((err) => {
  console.error("\nErro inesperado:", err.message);
  console.error(err.stack);
  process.exit(1);
});
