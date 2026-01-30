/**
 * Component metadata schema.
 */

import { z } from "zod";

/**
 * Valid component types.
 */
export const ComponentTypes = ["skills", "agents", "hooks", "rules"] as const;
export type ComponentType = (typeof ComponentTypes)[number];

/**
 * Singular form of component types.
 */
export const ComponentTypeSingular: Record<ComponentType, string> = {
  skills: "skill",
  agents: "agent",
  hooks: "hook",
  rules: "rule",
};

/**
 * Schema for component dependencies.
 */
export const ComponentDependenciesSchema = z.object({
  skills: z.array(z.string()).default([]),
  agents: z.array(z.string()).default([]),
  hooks: z.array(z.string()).default([]),
  rules: z.array(z.string()).default([]),
});

export type ComponentDependencies = z.infer<typeof ComponentDependenciesSchema>;

/**
 * Schema for component metadata (skill.json, agent.json, etc.).
 */
export const ComponentMetadataSchema = z
  .object({
    name: z.string().min(1, "Name is required"),
    description: z.string().optional(),
    dependencies: ComponentDependenciesSchema.default({
      skills: [],
      agents: [],
      hooks: [],
      rules: [],
    }),
  })
  .passthrough(); // Allow extra fields

export type ComponentMetadata = z.infer<typeof ComponentMetadataSchema>;

/**
 * Resolved component information.
 */
export interface ResolvedComponent {
  name: string;
  type: "shared" | "local";
  sourcePath: string;
  files: string[];
  metadata?: ComponentMetadata;
}

/**
 * Create component metadata with defaults.
 */
export function createComponentMetadata(
  name: string,
  options: Partial<Omit<ComponentMetadata, "name">> = {}
): ComponentMetadata {
  return ComponentMetadataSchema.parse({
    name,
    ...options,
  });
}

/**
 * Create empty component dependencies.
 */
export function createComponentDependencies(
  deps: Partial<ComponentDependencies> = {}
): ComponentDependencies {
  return ComponentDependenciesSchema.parse(deps);
}

/**
 * Get singular form of component type.
 */
export function getSingularType(type: ComponentType): string {
  return ComponentTypeSingular[type];
}

/**
 * Parse component reference (e.g., "skill:my-skill" or "my-skill").
 */
export function parseComponentRef(ref: string): {
  type: ComponentType | null;
  name: string;
} {
  if (ref.includes(":")) {
    const [typeStr, name] = ref.split(":", 2);
    const type = `${typeStr}s` as ComponentType;
    if (ComponentTypes.includes(type)) {
      return { type, name: name ?? "" };
    }
  }
  return { type: null, name: ref };
}
