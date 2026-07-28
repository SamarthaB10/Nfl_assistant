import { z } from "zod";

const displayName = z.string().trim().min(1).max(50);
export const publicUsernameSchema = z
  .string()
  .trim()
  .toLowerCase()
  .min(3)
  .max(24)
  .regex(
    /^[a-z0-9_]+$/,
    "Use only lowercase letters, numbers, and underscores.",
  );

export const signupSchema = z.object({
  email: z.string().trim().toLowerCase().email().max(254),
  username: publicUsernameSchema,
  displayName,
  password: z.string().min(8).max(128),
});

export const profileUpdateSchema = z.object({
  displayName,
  about: z.string().trim().max(300),
});

export const loginSchema = z.object({
  email: z.string().trim().toLowerCase().email().max(254),
  password: z.string().min(1).max(128),
});

export type SignupInput = z.infer<typeof signupSchema>;
export type ProfileUpdateInput = z.infer<typeof profileUpdateSchema>;
export type LoginInput = z.infer<typeof loginSchema>;
