/**
 * cpm link and unlink commands
 */

import { Command } from "commander";
import { cwd } from "node:process";
import { join } from "node:path";
import { parseComponentRef } from "../schemas/index.js";
import {
  loadCpmConfig,
  loadComponentMetadata,
  saveComponentMetadata,
  pathExists,
} from "../core/index.js";
import { success, error, warning } from "../utils/index.js";

export const linkCommand = new Command("link")
  .description("Link dependencies to an existing shared component")
  .argument("<dependencies>", "Dependencies to link (comma-separated)")
  .requiredOption("-t, --to <target>", "Target component (e.g., skill:my-skill)")
  .action(async (dependencies: string, options: { to: string }) => {
    try {
      const repoRoot = cwd();
      const cpmConfig = await loadCpmConfig(repoRoot);

      // Parse target
      const { type: targetType, name: targetName } = parseComponentRef(
        options.to
      );

      if (!targetType) {
        error("Target type required (e.g., skill:my-skill)");
        process.exit(1);
      }

      // Verify target exists
      const targetPath = join(
        repoRoot,
        cpmConfig.sharedDir,
        targetType,
        targetName
      );
      if (!(await pathExists(targetPath))) {
        error(`Target not found: ${targetType}/${targetName}`);
        process.exit(1);
      }

      // Load target metadata
      let metadata = await loadComponentMetadata(
        targetType,
        targetName,
        repoRoot
      );

      if (!metadata) {
        error(`Cannot load metadata for: ${targetType}/${targetName}`);
        process.exit(1);
      }

      // Parse dependencies
      const deps = dependencies.split(",").map((d) => d.trim());

      for (const dep of deps) {
        const { type: depType, name: depName } = parseComponentRef(dep);

        if (!depType) {
          warning(`Skipping invalid dependency: ${dep}`);
          continue;
        }

        // Verify dependency exists
        const depPath = join(
          repoRoot,
          cpmConfig.sharedDir,
          depType,
          depName
        );
        if (!(await pathExists(depPath))) {
          warning(`Dependency not found: ${depType}/${depName}`);
          continue;
        }

        // Add to metadata
        if (!metadata.dependencies[depType].includes(depName)) {
          metadata.dependencies[depType].push(depName);
          success(`Linked ${depType}/${depName} to ${targetType}/${targetName}`);
        } else {
          warning(`Already linked: ${depType}/${depName}`);
        }
      }

      // Save updated metadata
      await saveComponentMetadata(metadata, targetType, targetName, repoRoot);
    } catch (err) {
      error(`Failed to link: ${(err as Error).message}`);
      process.exit(1);
    }
  });

export const unlinkCommand = new Command("unlink")
  .description("Remove dependencies from an existing shared component")
  .argument("<dependencies>", "Dependencies to unlink (comma-separated)")
  .requiredOption(
    "-f, --from <target>",
    "Target component (e.g., skill:my-skill)"
  )
  .action(async (dependencies: string, options: { from: string }) => {
    try {
      const repoRoot = cwd();
      const cpmConfig = await loadCpmConfig(repoRoot);

      // Parse target
      const { type: targetType, name: targetName } = parseComponentRef(
        options.from
      );

      if (!targetType) {
        error("Target type required (e.g., skill:my-skill)");
        process.exit(1);
      }

      // Verify target exists
      const targetPath = join(
        repoRoot,
        cpmConfig.sharedDir,
        targetType,
        targetName
      );
      if (!(await pathExists(targetPath))) {
        error(`Target not found: ${targetType}/${targetName}`);
        process.exit(1);
      }

      // Load target metadata
      let metadata = await loadComponentMetadata(
        targetType,
        targetName,
        repoRoot
      );

      if (!metadata) {
        error(`Cannot load metadata for: ${targetType}/${targetName}`);
        process.exit(1);
      }

      // Parse dependencies
      const deps = dependencies.split(",").map((d) => d.trim());

      for (const dep of deps) {
        const { type: depType, name: depName } = parseComponentRef(dep);

        if (!depType) {
          warning(`Skipping invalid dependency: ${dep}`);
          continue;
        }

        // Remove from metadata
        const index = metadata.dependencies[depType].indexOf(depName);
        if (index !== -1) {
          metadata.dependencies[depType].splice(index, 1);
          success(
            `Unlinked ${depType}/${depName} from ${targetType}/${targetName}`
          );
        } else {
          warning(`Not linked: ${depType}/${depName}`);
        }
      }

      // Save updated metadata
      await saveComponentMetadata(metadata, targetType, targetName, repoRoot);
    } catch (err) {
      error(`Failed to unlink: ${(err as Error).message}`);
      process.exit(1);
    }
  });
