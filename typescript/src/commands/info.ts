/**
 * cpm info command
 */

import { Command } from "commander";

const PURPLE = "\x1b[35m";
const CYAN = "\x1b[36m";
const YELLOW = "\x1b[33m";
const WHITE = "\x1b[37m";
const BOLD = "\x1b[1m";
const DIM = "\x1b[2m";
const RESET = "\x1b[0m";

const banner = `
${PURPLE}${BOLD}
    ██████╗██████╗ ███╗   ███╗
   ██╔════╝██╔══██╗████╗ ████║
   ██║     ██████╔╝██╔████╔██║
   ██║     ██╔═══╝ ██║╚██╔╝██║
   ╚██████╗██║     ██║ ╚═╝ ██║
    ╚═════╝╚═╝     ╚═╝     ╚═╝
${RESET}
${CYAN}${BOLD}  Claude Project Manager${RESET}
${DIM}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}

${WHITE}  Manage mono repos with multiple Claude Code
  projects. Share skills, agents, hooks, and
  rules across projects without duplication.${RESET}

${DIM}  ─────────────────────────────────────────${RESET}

${YELLOW}  Quick Start:${RESET}
${DIM}  $ ${WHITE}cpm init my-monorepo${RESET}
${DIM}  $ ${WHITE}cpm create project web-app${RESET}
${DIM}  $ ${WHITE}cpm create skill logging${RESET}
${DIM}  $ ${WHITE}cpm add skill:logging --to web-app${RESET}

${DIM}  ─────────────────────────────────────────${RESET}

${PURPLE}  ◆${RESET} ${DIM}Crafted by${RESET} ${CYAN}Transilience.ai${RESET}
${PURPLE}  ◆${RESET} ${DIM}Authored by${RESET} ${WHITE}Aman Agarwal${RESET}
${DIM}    github.com/amanagarwal041${RESET}

${DIM}  ─────────────────────────────────────────${RESET}

${DIM}  Docs:${RESET}    ${CYAN}https://cpm.transilience.ai${RESET}
${DIM}  GitHub:${RESET}  ${CYAN}https://github.com/transilienceai/cpm${RESET}

${DIM}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}
`;

export function printBanner(): void {
  console.log(banner);
}

export const infoCommand = new Command("info")
  .description("Show CPM information banner")
  .action(() => {
    printBanner();
  });
