"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { Loader2, LogOut } from "lucide-react";
import { toast } from "sonner";

import { leaveNeighbourhood } from "@/lib/api/neighbourhood";
import { useUserContext } from "@/hooks/use-user-context";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";



export default function PropertySettingsPage() {
  const { propertyId } = useParams<{ propertyId: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data: userContext, isLoading } = useUserContext();

  const [isLeaving, setIsLeaving] = useState(false);

  const property = userContext?.properties.find(
    (item) => item.id === propertyId,
  );

  async function handleLeaveNeighbourhood() {
    if (
      !property?.is_admin ||
      !property.neighbourhood
    ) {
      return;
    }

    setIsLeaving(true);

    try {
      await leaveNeighbourhood({
        neighbourhoodId: property.neighbourhood.id,
        propertyId: property.id,
      });

      await queryClient.invalidateQueries({
        queryKey: ["userContext"],
      });

      toast.success("Property left the neighbourhood");

      router.replace(
        `/dashboard/properties/${property.id}/cameras`,
      );
    } catch (error: unknown) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Failed to leave neighbourhood",
      );
    } finally {
      setIsLeaving(false);
    }
  }


  if (isLoading) {
    return (
      <main className="flex min-h-full items-center justify-center">
        <Loader2 className="size-5 animate-spin text-primary" />
      </main>
    );
  }

  if (!property) {
    return (
      <main className="p-8">
        <p className="text-destructive">Property not found.</p>
      </main>
    );
  }

    return (
    <main className="min-h-full bg-background px-6 py-8 text-foreground md:px-8">
      <div className="mx-auto w-full max-w-4xl">
        <header className="border-b border-border pb-6">
          <p className="text-sm text-primary">My home</p>

          <h1 className="mt-2 text-2xl font-semibold">
            Property settings
          </h1>

          <p className="mt-1 text-sm text-muted-foreground">
            Manage settings for {property.address}.
          </p>
        </header>

        {property.is_admin && property.neighbourhood && (
          <section className="mt-8 rounded-xl border border-destructive/30 bg-card p-6">
            <h2 className="text-lg font-semibold text-destructive">
              Danger zone
            </h2>

            <div className="mt-5 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
              <div>
                <h3 className="font-medium">
                  Leave {property.neighbourhood.name}
                </h3>

                <p className="mt-1 text-sm text-muted-foreground">
                  Disconnect this property from the neighbourhood and
                  remove its access to neighbourhood alerts and analytics.
                </p>
              </div>

              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <button
                    type="button"
                    className="inline-flex h-10 shrink-0 items-center justify-center rounded-md border border-destructive/40 px-4 text-sm font-medium text-destructive hover:bg-destructive/10"
                  >
                    <LogOut className="mr-2 size-4" />
                    Leave neighbourhood
                  </button>
                </AlertDialogTrigger>

                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>
                      Leave neighbourhood?
                    </AlertDialogTitle>

                    <AlertDialogDescription>
                      {property.address} will leave{" "}
                      {property.neighbourhood.name}. You will need to
                      submit another join request to reconnect it later.
                    </AlertDialogDescription>
                  </AlertDialogHeader>

                  <AlertDialogFooter>
                    <AlertDialogCancel disabled={isLeaving}>
                      Cancel
                    </AlertDialogCancel>

                    <AlertDialogAction
                      disabled={isLeaving}
                      onClick={(event) => {
                        event.preventDefault();
                        void handleLeaveNeighbourhood();
                      }}
                      className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                    >
                      {isLeaving ? (
                        <>
                          <Loader2 className="mr-2 size-4 animate-spin" />
                          Leaving...
                        </>
                      ) : (
                        "Leave neighbourhood"
                      )}
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          </section>
        )}
      </div>
    </main>
  );

}
