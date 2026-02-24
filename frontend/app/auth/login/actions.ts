"use server";

import { createClient } from "@/lib/supabase/server";

export async function signIn(formData: FormData): Promise<string | null> {
  const email = formData.get("email") as string;
  const password = formData.get("password") as string;

  if (!email || !password) {
    return "Email and password are required.";
  }

  const supabase = await createClient();
  const { error } = await supabase.auth.signInWithPassword({ email, password });

  if (error) {
    return error.message;
  }

  return null;
}
