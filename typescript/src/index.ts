/**
 * CLDPM - Claude Project Manager
 *
 * An SDK and CLI for managing mono repos with multiple Claude Code projects.
 *
 * @example
 * ```typescript
 * import { loadCldpmConfig, resolveProject, listProjects } from "cldpm";
 *
 * // Load configuration
 * const config = await loadCldpmConfig("/path/to/monorepo");
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
  // CLDPM Config
  CldpmConfigSchema,
  type CldpmConfig,
  createCldpmConfig,
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
  loadCldpmConfig,
  saveCldpmConfig,
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

// AI Rules
export {
  createAiRules,
  appendToClaudeMd,
  getCursorRulesContent,
  getClineRulesContent,
  getWindsurfRulesContent,
  getCopilotInstructionsContent,
  getClaudeMdSection,
  getClaudeMdContent,
  // Section markers
  CLDPM_SECTION_START,
  CLDPM_SECTION_END,
  CLDPM_SECTION_MARKER,
} from "./ai-rules.js";

// Version
export const VERSION = "0.1.3";
