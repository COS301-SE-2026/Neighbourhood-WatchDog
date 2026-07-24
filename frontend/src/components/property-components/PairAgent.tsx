"use client"

import { useState } from "react";
import { getPairingToken } from "@/lib/api/pairAgent";

interface PairAgentProps{
	propertyId: string
}

export default function PairAgent({
	propertyId
}: PairAgentProps){
	
	const [error, setError] = useState<string|null>(null)
	const [loading, setLoading] = useState(false)
	const [token, setToken] = useState<string|null>(null)
	
	const getToken = async () => {
		try{
			setLoading(true)
			setError(null)
			const tokenResponse = await getPairingToken(propertyId)

			if (!tokenResponse || tokenResponse.status !== 200 || !tokenResponse.data){
				throw new Error("Could not get token. Please try again.");
			}

			setToken(tokenResponse.data.token)
		} catch (error) {
			setError(error instanceof Error ? error.message : "An error occurred")
		} finally {
			setLoading(false)
		}
	}

	return (
		<div className="max-w-md mx-auto my-8 p-6 bg-white border border-gray-200 rounded-xl shadow-sm">
			{loading && (
				<div className="mb-4 p-3 bg-blue-50 text-blue">
						Fetching your token...
				</div>
			)}
			{error && (
				<div>
					{error}
				</div>
			)}

			{!token ? (
				<div>
					<h2>Request a pairing token</h2>
					<p>Generate a secure pairing token linked to your property.</p>
					<button
						onClick={getToken}
						disabled={loading}
					>
						{loading ? "Requesting..." : "Generate Token"}
					</button>
				</div>
			) : (
				<div>
					<h4>Here is your token</h4>
					<p className="text-lg font-bold">
						{token}
					</p>
					<button
						onClick={getToken}
						disabled={loading}
					>
						Regenerate Token
					</button>
				</div>
			)}
		</div>
	)
    
}