import { apiCall } from "./client";
import { CurrentUserContextResSchema, type CurrentUserContextRes } from "@/lib/validators/user";

export async function fetchMyContext(): Promise<CurrentUserContextRes> {
    const result = await apiCall<unknown>("/users/me/context", { method: "GET" });
    return CurrentUserContextResSchema.parse(result);
}