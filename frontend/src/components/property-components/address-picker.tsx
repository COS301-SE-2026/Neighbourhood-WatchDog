"use client";

import { useState } from "react";

import { Input } from "@/components/ui/input";

export type SelectedAddress = {
    displayName: string;
    latitude: number;
    longitude: number;
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

    const handleChange = (nextQuery: string) => {
        setQuery(nextQuery);

        // Typing a new address clears the previous selection.
        onSelect(null);
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

            <Input
                id="property-address"
                value={query}
                onChange={(event) => handleChange(event.target.value)}
                placeholder="Search for an address"
                autoComplete="off"
                aria-invalid={Boolean(error)}
                aria-describedby={
                    error ? "property-address-error" : undefined
                }
            />

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
