/**
 * CLDPM root configuration schema.
 */

import { z } from "zod";

/**
 * Schema for cldpm.json configuration file.
 */
export const CldpmConfigSchema = z.object({
  name: z.string().min(1, "Name is required"),
  version: z.string().default("1.0.0"),
  projectsDir: z.string().default("projects"),
  sharedDir: z.string().default("shared"),
});

export type CldpmConfig = z.infer<typeof CldpmConfigSchema>;

/**
 * Create a CldpmConfig with defaults.
 */
export function createCldpmConfig(
  name: string,
  options: Partial<Omit<CldpmConfig, "name">> = {}
): CldpmConfig {
  return CldpmConfigSchema.parse({
    name,
    ...options,
  });
}
