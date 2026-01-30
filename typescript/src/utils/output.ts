/**
 * Output formatting utilities.
 */

import chalk from "chalk";
import type { ComponentType } from "../schemas/index.js";
import type { ResolvedProject } from "../core/resolver.js";

/**
 * Print success message.
 */
export function success(message: string): void {
  console.log(chalk.green("✓"), message);
}

/**
 * Print error message.
 */
export function error(message: string): void {
  console.error(chalk.red("✗"), message);
}

/**
 * Print warning message.
 */
export function warning(message: string): void {
  console.log(chalk.yellow("⚠"), message);
}

/**
 * Print info message.
 */
export function info(message: string): void {
  console.log(chalk.blue("ℹ"), message);
}

/**
 * Print a project as a tree.
 */
export function printProjectTree(project: ResolvedProject): void {
  console.log(chalk.bold(project.name));
  console.log("├── Shared");

  const componentTypes: ComponentType[] = ["skills", "agents", "hooks", "rules"];

  for (let i = 0; i < componentTypes.length; i++) {
    const compType = componentTypes[i]!;
    const components = project.shared[compType];
    const isLastType = i === componentTypes.length - 1;
    const typePrefix = isLastType ? "│   └── " : "│   ├── ";

    if (components.length === 0) {
      continue;
    }

    console.log(`${typePrefix}${compType}`);

    for (let j = 0; j < components.length; j++) {
      const comp = components[j]!;
      const isLast = j === components.length - 1;
      const compPrefix = isLastType
        ? isLast
          ? "│       └── "
          : "│       ├── "
        : isLast
          ? "│   │   └── "
          : "│   │   ├── ";
      console.log(`${compPrefix}${comp.name}`);
    }
  }

  console.log("└── Local");

  for (let i = 0; i < componentTypes.length; i++) {
    const compType = componentTypes[i]!;
    const components = project.local[compType];
    const isLastType = i === componentTypes.length - 1;
    const typePrefix = isLastType ? "    └── " : "    ├── ";

    if (components.length === 0) {
      continue;
    }

    console.log(`${typePrefix}${compType}`);

    for (let j = 0; j < components.length; j++) {
      const comp = components[j]!;
      const isLast = j === components.length - 1;
      const compPrefix = isLastType
        ? isLast
          ? "        └── "
          : "        ├── "
        : isLast
          ? "    │   └── "
          : "    │   ├── ";
      console.log(`${compPrefix}${comp.name}`);
    }
  }

  // Check if all empty
  const hasShared = componentTypes.some(
    (t) => project.shared[t].length > 0
  );
  const hasLocal = componentTypes.some(
    (t) => project.local[t].length > 0
  );

  if (!hasShared) {
    console.log("│   └── (none)");
  }
  if (!hasLocal) {
    console.log("    └── (none)");
  }
}

/**
 * Print a project as JSON.
 */
export function printProjectJson(project: ResolvedProject): void {
  console.log(JSON.stringify(project, null, 2));
}
