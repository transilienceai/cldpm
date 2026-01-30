/**
 * CPM Schemas - Type definitions and validation.
 */

export {
  CpmConfigSchema,
  type CpmConfig,
  createCpmConfig,
} from "./cpm.js";

export {
  ProjectConfigSchema,
  ProjectDependenciesSchema,
  type ProjectConfig,
  type ProjectDependencies,
  createProjectConfig,
  createProjectDependencies,
} from "./project.js";

export {
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
} from "./component.js";
