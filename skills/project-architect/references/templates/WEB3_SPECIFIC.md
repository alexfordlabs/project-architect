---
template_name: WEB3_SPECIFIC
generate_when: "decisions.project.type == 'web3'"
required_decisions: [web3.chain, web3.contract_language]
optional_decisions: [web3.dev_framework, web3.indexing, web3.wallet_integration, web3.upgradeability, web3.audits]
depends_on: []
revision_triggers: [web3.chain, web3.contract_language, web3.dev_framework, web3.upgradeability]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Web3 Specific: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [🌐 Chain & Network](#chain-network)
- [Contract Language & Compiler](#contract-language-compiler)
- [Dev Framework (Foundry / Hardhat / Anchor)](#dev-framework-foundry-hardhat-anchor)
- [🏗️ Contract Architecture (modules, interfaces)](#contract-architecture-modules-interfaces)
- [Upgradeability Pattern](#upgradeability-pattern)
- [🗄️ Storage Strategy](#storage-strategy)
- [Indexing (The Graph / Goldsky / custom)](#indexing-the-graph-goldsky-custom)
- [🔧 Wallet Integration](#wallet-integration)
- [Audit Plan](#audit-plan)
- [Bug Bounty](#bug-bounty)
- [↻ Revision Log](#revision-log)

## 🌐 Chain & Network
Chosen chain(s) (Ethereum mainnet, L2 — Base / Arbitrum / Optimism / zkSync, alt-L1 — Solana / Sui / Aptos, Cosmos appchain), network mode (mainnet, testnet, devnet), and rationale.

## Contract Language & Compiler
Smart-contract language (Solidity, Vyper, Rust for Solana/Anchor, Move for Sui/Aptos, Cairo for Starknet), compiler version pinning, and optimizer settings.

## Dev Framework (Foundry / Hardhat / Anchor)
Development framework (Foundry, Hardhat, Truffle, Anchor for Solana, Sui Move CLI), local node strategy (Anvil, Hardhat Network, surfnet), and fixture management.

## 🏗️ Contract Architecture (modules, interfaces)
Module breakdown (registry / governance / token / vault / etc.), interface contracts between modules, library reuse (OpenZeppelin, Solady, Solmate), and reentrancy posture.

## Upgradeability Pattern
Upgradeability pattern (immutable, Transparent Proxy, UUPS, Diamond / EIP-2535, Beacon, immutable with migration), admin keys, timelock, and emergency pause.

## 🗄️ Storage Strategy
On-chain storage layout discipline, storage gaps for upgrades, packed-storage optimization, and off-chain storage (IPFS, Arweave, S3) for media or large data.

## Indexing (The Graph / Goldsky / custom)
Indexing approach (The Graph subgraphs, Goldsky, Ponder, custom indexer), event design for indexability, and reorg-handling strategy.

## 🔧 Wallet Integration
Wallet stack (RainbowKit, ConnectKit, WalletConnect, Web3Modal, Privy, Dynamic, embedded wallets), supported wallets, and signing UX (EIP-712 typed data, gasless via paymaster).

## Audit Plan
Audit scope, target firms (Trail of Bits, OpenZeppelin, Spearbit, Code4rena, Sherlock contest), timing relative to launch, fix-verification cycle, and re-audit cadence after upgrades.

## Bug Bounty
Bug-bounty program (Immunefi, HackerOne), severity ladder, payout schedule, disclosure policy, and SLA for triage.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
