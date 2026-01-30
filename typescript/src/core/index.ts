/**
 * CLDPM Core - Configuration, resolution, and linking.
 */

export {
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
} from "./config.js";

export {
  resolveProject,
  resolveComponent,
  resolveLocalComponent,
  getLocalComponentsInProject,
  listSharedComponents,
  resolveComponentDependencies,
  getAllDependenciesForComponent,
  type ResolvedProject,
} from "./resolver.js";

export {
  createSymlink,
  removeProjectLinks,
  updateComponentGitignore,
  syncProjectLinks,
  addComponentLink,
  removeComponentLink,
  getLocalComponents,
  getSharedComponents,
} from "./linker.js";
