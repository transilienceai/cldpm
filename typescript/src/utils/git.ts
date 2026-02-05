/**
 * Git utility functions for remote repository operations.
 */

import { spawn } from "node:child_process";
import * as fs from "node:fs/promises";
import * as path from "node:path";
import * as os from "node:os";
import { warning } from "./output.js";

/**
 * Get GitHub token from environment variables.
 * Checks GITHUB_TOKEN and GH_TOKEN in that order.
 */
export function getGithubToken(): string | undefined {
  return process.env.GITHUB_TOKEN || process.env.GH_TOKEN;
}

/**
 * Parse a repository URL to extract repo URL, optional path, and branch.
 *
 * Supports formats:
 * - https://github.com/owner/repo
 * - https://github.com/owner/repo/tree/branch
 * - https://github.com/owner/repo/tree/branch/path/to/project
 * - github.com/owner/repo
 * - owner/repo (assumes GitHub)
 */
export function parseRepoUrl(
  url: string
): { repoUrl: string; subpath: string | null; branch: string | null } {
  const originalUrl = url;
  let branch: string | null = null;
  let subpath: string | null = null;

  // Handle shorthand owner/repo format
  if (
    !url.startsWith("http://") &&
    !url.startsWith("https://") &&
    !url.startsWith("git@") &&
    url.includes("/")
  ) {
    if (url.split("/").length === 2) {
      // Simple owner/repo format
      url = `https://github.com/${url}`;
    } else if (!url.startsWith("github.com")) {
      url = `https://${url}`;
    }
  }

  // Add https:// if missing
  if (url.startsWith("github.com")) {
    url = `https://${url}`;
  }

  // Parse the URL
  let parsedUrl: URL;
  try {
    parsedUrl = new URL(url);
  } catch {
    throw new Error(`Invalid repository URL: ${originalUrl}`);
  }

  const pathParts = parsedUrl.pathname.replace(/^\/|\/$/g, "").split("/");

  if (pathParts.length >= 2) {
    const owner = pathParts[0];
    let repo = pathParts[1]!;

    // Remove .git suffix if present
    if (repo.endsWith(".git")) {
      repo = repo.slice(0, -4);
    }

    // Check for /tree/branch/path pattern
    if (pathParts.length > 3 && pathParts[2] === "tree") {
      branch = pathParts[3]!;
      if (pathParts.length > 4) {
        subpath = pathParts.slice(4).join("/");
      }
    }

    const repoUrl = `https://${parsedUrl.hostname}/${owner}/${repo}.git`;
    return { repoUrl, subpath, branch };
  }

  throw new Error(`Invalid repository URL: ${originalUrl}`);
}

/**
 * Execute a command and return the result.
 */
async function execCommand(
  command: string,
  args: string[],
  options: { cwd?: string; env?: NodeJS.ProcessEnv } = {}
): Promise<{ stdout: string; stderr: string }> {
  return new Promise((resolve, reject) => {
    const proc = spawn(command, args, {
      cwd: options.cwd,
      env: { ...process.env, ...options.env, GIT_TERMINAL_PROMPT: "0" },
    });

    let stdout = "";
    let stderr = "";

    proc.stdout?.on("data", (data) => {
      stdout += data.toString();
    });

    proc.stderr?.on("data", (data) => {
      stderr += data.toString();
    });

    proc.on("close", (code) => {
      if (code === 0) {
        resolve({ stdout, stderr });
      } else {
        const error = new Error(`Command failed with code ${code}: ${stderr}`);
        (error as Error & { stderr: string }).stderr = stderr;
        reject(error);
      }
    });

    proc.on("error", reject);
  });
}

/**
 * Check if the current Git version supports sparse checkout with partial clone.
 * Requires Git 2.25+ for reliable sparse checkout with --no-cone mode.
 */
export async function hasSparseCloneSupport(): Promise<boolean> {
  try {
    const { stdout } = await execCommand("git", ["--version"]);

    // Parse version from "git version X.Y.Z"
    const versionStr = stdout.trim()?.match(/\d+\.\d+\.\d+/)?.[0] || "";
    const versionStrParts = versionStr.split(".");
    const versionStrMajor = parseInt(versionStrParts[0] || "0", 10);
    const versionStrMinor = parseInt(versionStrParts[1] || "0", 10);
    // Require Git 2.25+ for reliable sparse checkout
    return versionStrMajor > 2 || (versionStrMajor === 2 && versionStrMinor >= 25);
  } catch {
    return false;
  }
}

/**
 * Create a temporary directory with the given prefix.
 */
async function createTempDir(prefix: string): Promise<string> {
  const tempBase = os.tmpdir();
  const tempDir = path.join(tempBase, `${prefix}${Date.now()}-${Math.random().toString(36).slice(2)}`);
  await fs.mkdir(tempDir, { recursive: true });
  return tempDir;
}

/**
 * Clean up a temporary directory.
 */
export async function cleanupTempDir(tempDir: string): Promise<void> {
  const tempBase = os.tmpdir();
  if (tempDir.startsWith(tempBase)) {
    await fs.rm(tempDir, { recursive: true, force: true });
  }
}

/**
 * Copy a directory recursively.
 */
async function copyDir(src: string, dest: string): Promise<void> {
  await fs.mkdir(dest, { recursive: true });
  const entries = await fs.readdir(src, { withFileTypes: true });

  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);

    if (entry.isDirectory()) {
      await copyDir(srcPath, destPath);
    } else {
      await fs.copyFile(srcPath, destPath);
    }
  }
}

/**
 * Download specific paths using sparse checkout with partial clone.
 *
 * Uses Git's partial clone (--filter=blob:none) with sparse checkout to
 * download only the requested paths, significantly reducing data transfer
 * for large repositories.
 */
export async function sparseClonePaths(
  repoUrl: string,
  paths: string[],
  targetDir: string,
  branch?: string,
  token?: string
): Promise<void> {
  const tempClone = await createTempDir("cldpm-sparse-");

  try {
    // Inject token for auth
    let authUrl = repoUrl;
    if (token && repoUrl.includes("github.com")) {
      authUrl = repoUrl.replace(
        "https://github.com",
        `https://${token}@github.com`
      );
    }

    // Step 1: Partial clone (tree-only, no blobs initially)
    const cloneArgs = [
      "clone",
      "--filter=blob:none",
      "--sparse",
      "--depth",
      "1",
    ];
    if (branch) {
      cloneArgs.push("--branch", branch);
    }
    cloneArgs.push(authUrl, tempClone);

    await execCommand("git", cloneArgs);

    // Step 2: Configure sparse checkout for exact paths
    const sparseArgs = ["sparse-checkout", "set", "--no-cone", ...paths];
    await execCommand("git", sparseArgs, { cwd: tempClone });

    // Step 3: Copy files to target (excluding .git)
    await fs.mkdir(targetDir, { recursive: true });
    for (const p of paths) {
      const src = path.join(tempClone, p);
      try {
        await fs.access(src);
        const dst = path.join(targetDir, p);
        await fs.mkdir(path.dirname(dst), { recursive: true });

        const stat = await fs.stat(src);
        if (stat.isDirectory()) {
          await copyDir(src, dst);
        } else {
          await fs.copyFile(src, dst);
        }
      } catch {
        // Path doesn't exist in repo, skip
      }
    }
  } finally {
    await cleanupTempDir(tempClone);
  }
}

/**
 * Download specific paths to a temporary directory.
 */
export async function sparseCloneToTemp(
  repoUrl: string,
  paths: string[],
  branch?: string,
  token?: string
): Promise<string> {
  const tempDir = await createTempDir("cldpm-");
  await sparseClonePaths(repoUrl, paths, tempDir, branch, token);
  return tempDir;
}

/**
 * Clone a repository to a temporary directory (full clone, fallback).
 */
export async function cloneToTemp(
  repoUrl: string,
  branch?: string,
  token?: string
): Promise<string> {
  const tempDir = await createTempDir("cldpm-");

  // Inject token for auth
  let authUrl = repoUrl;
  if (token && repoUrl.includes("github.com")) {
    authUrl = repoUrl.replace(
      "https://github.com",
      `https://${token}@github.com`
    );
  }

  const cloneArgs = ["clone", "--depth", "1"];
  if (branch) {
    cloneArgs.push("--branch", branch);
  }
  cloneArgs.push(authUrl, tempDir);

  await execCommand("git", cloneArgs);

  return tempDir;
}
