import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { PlaygroundPage } from "@/components/play-ground";
import { useAuthStore } from "@/stores/auth-store";
import { useEffect } from "react";
import { z } from "zod";
import { useGetCurrentUser } from "@/hooks/api/user/useGetCurrentUser";
import { isCoordinatorRole } from "@/lib/roles";
import { app as firebaseApp } from "@/config/firebase";
import { isDevelopment } from "@/shared/app";
export const Route = createFileRoute("/home/")({
  validateSearch: z.object({
    question: z.string().optional(),
    request: z.string().optional(),
    comment: z.string().optional(),
    history:z.string().optional(),
    expertId:z.string().optional(),
    questionType:z.string().optional()
  }),
  component: RouteComponent,
});

function RouteComponent() {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const { data: currentUser, isLoading, error } = useGetCurrentUser({});

  const noFirebase = !firebaseApp || isDevelopment;

  useEffect(() => {
    if (!user) {
      navigate({ to: "/auth" });
      return;
    }
    if (noFirebase) return; // skip role checks in dev mode
    if (currentUser?.role === "pae_expert") {
      navigate({ to: "/pae-expert" });
      return;
    }
    if (isCoordinatorRole(currentUser?.role)) {
      navigate({
        to: "/user/$userId",
        params: { userId: currentUser?._id || user.uid },
      });
      return;
    }
  }, [user, currentUser, navigate, noFirebase]);

  if (!user) return null;
  if (!noFirebase && isLoading) return null;
  if (!noFirebase && currentUser?.role === "pae_expert") return null;
  if (!noFirebase && isCoordinatorRole(currentUser?.role)) return null;

  return (
    <div className="min-h-screen min-w-screen p-4 relative flex flex-col overflow-hidden">
      <PlaygroundPage />
    </div>
  );
}
