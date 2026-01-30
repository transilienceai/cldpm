#!/usr/bin/env node
/**
 * CLDPM CLI - Command Line Interface
 *
 * Crafted by Transilience.ai
 * Authored by Aman Agarwal (https://github.com/amanagarwal041)
 */

import { Command } from "commander";
import { VERSION } from "./index.js";
import { initCommand } from "./commands/init.js";
import { createCommand } from "./commands/create.js";
import { addCommand } from "./commands/add.js";
import { removeCommand } from "./commands/remove.js";
import { getCommand } from "./commands/get.js";
import { cloneCommand } from "./commands/clone.js";
import { syncCommand } from "./commands/sync.js";
import { linkCommand, unlinkCommand } from "./commands/link.js";
import { infoCommand, printBanner } from "./commands/info.js";

const program = new Command();

program
  .name("cldpm")
  .description(
    `CLDPM - Claude Project Manager

An SDK and CLI for managing mono repos with multiple Claude Code projects.
Supports both shared components (reusable across projects) and local
components (project-specific).

Component Types:
  - Shared: Stored in shared/, symlinked to projects, reusable
  - Local:  Stored in .claude/, project-specific, committed directly

Quick Start:
  cldpm init my-monorepo              # Create new mono repo
  cldpm create project my-app         # Create new project
  cldpm add skill:common --to my-app  # Add shared component
  cldpm get my-app                    # View project info
  cldpm sync --all                    # Restore symlinks after git clone

Crafted by Transilience.ai
Authored by Aman Agarwal (https://github.com/amanagarwal041)`
  )
  .option("-v, --version", "Show version and info banner")
  .on("option:version", () => {
    printBanner();
    console.log(`  Version: ${VERSION}\n`);
    process.exit(0);
  });

// Register commands
program.addCommand(initCommand);
program.addCommand(createCommand);
program.addCommand(addCommand);
program.addCommand(removeCommand);
program.addCommand(getCommand);
program.addCommand(cloneCommand);
program.addCommand(syncCommand);
program.addCommand(linkCommand);
program.addCommand(unlinkCommand);
program.addCommand(infoCommand);

program.parse();
