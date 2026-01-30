/**
 * CPM root configuration schema.
 */

import { z } from "zod";

/**
 * Schema for cpm.json configuration file.
 */
export const CpmConfigSchema = z.object({
  name: z.string().min(1, "Name is required"),
  version: z.string().default("1.0.0"),
  projectsDir: z.string().default("projects"),
  sharedDir: z.string().default("shared"),
});

export type CpmConfig = z.infer<typeof CpmConfigSchema>;

/**
 * Create a CpmConfig with defaults.
 */
export function createCpmConfig(
  name: string,
  options: Partial<Omit<CpmConfig, "name">> = {}
): CpmConfig {
  return CpmConfigSchema.parse({
    name,
    ...options,
  });
}
