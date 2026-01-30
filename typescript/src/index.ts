/**
 * CPM - Claude Project Manager
 *
 * An SDK and CLI for managing mono repos with multiple Claude Code projects.
 *
 * @example
 * ```typescript
 * import { loadCpmConfig, resolveProject, listProjects } from "cpm";
 *
 * // Load configuration
 * const config = await loadCpmConfig("/path/to/monorepo");
 *
 * // List all projects
 * const projects = await listProjects("/path/to/monorepo");
 *
 * // Resolve a project
 * const project = await resolveProject("my-project", "/path/to/monorepo");
 * ```
 *
 * Crafted by Transilience.ai
 * Authored by Aman Agarwal (https://github.com/amanagarwal041)
 */

// Schemas
export {
  // CPM Config
  CpmConfigSchema,
  type CpmConfig,
  createCpmConfig,
  // Project Config
  ProjectConfigSchema,
  ProjectDependenciesSchema,
  type ProjectConfig,
  type ProjectDependencies,
  createProjectConfig,
  createProjectDependencies,
  // Component
  ComponentMetadataSchema,
  ComponentDependenciesSchema,
  ComponentTypes,
  ComponentTypeSingular,
  type ComponentType,
  type ComponentMetadata,
  type ComponentDependencies,
  type ResolvedComponent,
  createComponentMetadata,
  createComponentDependencies,
  getSingularType,
  parseComponentRef,
} from "./schemas/index.js";

// Core
export {
  // Config
  loadCpmConfig,
  saveCpmConfig,
  loadProjectConfig,
  saveProjectConfig,
  getProjectPath,
  listProjects,
  loadComponentMetadata,
  saveComponentMetadata,
  pathExists,
  isDirectory,
  // Resolver
  resolveProject,
  resolveComponent,
  resolveLocalComponent,
  getLocalComponentsInProject,
  listSharedComponents,
  resolveComponentDependencies,
  getAllDependenciesForComponent,
  type ResolvedProject,
  // Linker
  createSymlink,
  removeProjectLinks,
  updateComponentGitignore,
  syncProjectLinks,
  addComponentLink,
  removeComponentLink,
  getLocalComponents,
  getSharedComponents,
} from "./core/index.js";

// Utils
export {
  success,
  error,
  warning,
  info,
  printProjectTree,
  printProjectJson,
} from "./utils/index.js";

// Version
export const VERSION = "0.1.0";
