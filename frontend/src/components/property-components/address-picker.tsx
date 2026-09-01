"use client";

import { useEffect, useState } from "react";

import { Input } from "@/components/ui/input";
import { Spinner } from "../ui/spinner";

export type SelectedAddress = {
    displayName: string;
    latitude: number;
    longitude: number;
};

type NominatimResult = {
    place_id: number;
    display_name: string;
    lat: string;
    lon: string;
};

interface AddressPickerProps {
    value: SelectedAddress | null;
    onSelect: (address: SelectedAddress | null) => void;
    error?: string;
}

export function AddressPicker({
    value,
    onSelect,
    error,
}: AddressPickerProps) {
    const [query, setQuery] = useState(value?.displayName ?? "");
    const [results, setResults] = useState<NominatimResult[]>([]);
    const [isSearching, setIsSearching] = useState(false);
    const [searchError, setSearchError] = useState<string | null>(null);

    useEffect(() => {
        const searchTerm = query.trim();

        if (searchTerm.length < 3) {
            setResults([]);
            setSearchError(null);
            return;
        }

        if (value?.displayName === searchTerm) {
            setResults([]);
            return;
        }

        const controller = new AbortController();

        const timeout = window.setTimeout(async () => {
            setIsSearching(true);
            setSearchError(null);

            try {
                const searchParams = new URLSearchParams({
                    q: `${searchTerm}, South Africa`,
                    format: "jsonv2",
                    addressdetails: "1",
                    limit: "5",
                    countrycodes: "za",
                });

                const response = await fetch(
                    `https://nominatim.openstreetmap.org/search?${searchParams.toString()}`,
                    {
                        signal: controller.signal,
                        headers: {
                            Accept: "application/json",
                            "Accept-Language": "en",
                        },
                    },
                );

                if (!response.ok) {
                    throw new Error("Address search failed");
                }

                const data = (await response.json()) as NominatimResult[];
                setResults(data);
            } catch (error) {
                if (
                    error instanceof DOMException &&
                    error.name === "AbortError"
                ) {
                    return;
                }

                console.error("Address search failed:", error);
                setSearchError("Unable to search for addresses.");
            } finally {
                setIsSearching(false);
            }
        }, 500);

        return () => {
            window.clearTimeout(timeout);
            controller.abort();
        };
    }, [query, value?.displayName]);

    const handleQueryChange = (nextQuery: string) => {
        setQuery(nextQuery);
        setResults([]);
        setSearchError(null);
        onSelect(null);
    };

    const handleSelect = (result: NominatimResult) => {
        const selectedAddress: SelectedAddress = {
            displayName: result.display_name,
            latitude: Number(result.lat),
            longitude: Number(result.lon),
        };

        setQuery(selectedAddress.displayName);
        setResults([]);
        setSearchError(null);
        onSelect(selectedAddress);
    };

    return (
        <div className="space-y-2">
            <div>
                <label
                    htmlFor="property-address"
                    className="text-sm font-medium text-foreground"
                >
                    Property address
                </label>

                <p className="mt-1 text-xs text-muted-foreground">
                    Search for your address and select the correct result.
                </p>
            </div>

            <div className="relative">
                <Input
                    id="property-address"
                    value={query}
                    onChange={(event) =>
                        handleQueryChange(event.target.value)
                    }
                    placeholder="Search for an address"
                    autoComplete="off"
                    aria-invalid={Boolean(error)}
                    aria-describedby={
                        error ? "property-address-error" : undefined
                    }
                />

                {isSearching && (
                    <Spinner className="absolute right-3 top-1/2 size-4 -translate-y-1/2" />
                )}
            </div>

            {results.length > 0 && (
                <div className="overflow-hidden rounded-md border border-border bg-background">
                    {results.map((result) => (
                        <button
                            key={result.place_id}
                            type="button"
                            onClick={() => handleSelect(result)}
                            className="block w-full border-b border-border px-3 py-2 text-left text-sm last:border-b-0 hover:bg-muted"
                        >
                            {result.display_name}
                        </button>
                    ))}
                </div>
            )}

            {searchError && (
                <p className="text-xs text-threat">
                    {searchError}
                </p>
            )}

            {error && (
                <p
                    id="property-address-error"
                    className="text-xs text-threat"
                >
                    {error}
                </p>
            )}

            <p className="text-[11px] text-muted-foreground">
                Address search provided by OpenStreetMap Nominatim.
            </p>
        </div>
    );
}
