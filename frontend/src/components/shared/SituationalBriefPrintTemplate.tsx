"use client";

import Image from "next/image";
import logoImage from "@/assets/images/logo-mark-only.svg";
import type { SituationalBriefData } from "@/lib/api/alert";


interface SituationalBriefPrintTemplateProps {
    readonly brief: SituationalBriefData;

}


function formatBriefDate(value: string): string {

    try{
        return new Intl.DateTimeFormat("en-ZA", {
            dateStyle: "medium", 
            timeStyle: "short"
        }).format(new Date(value));

    } catch {
        return value;
    }

}



export function SituationalBriefPrintTemplate({brief}: SituationalBriefPrintTemplateProps) {

    const primaryAlert = brief.alerts[0];


    return (
        <article className="situational-brief-print hidden">
            <header className="brief-print-header">
                <div className="brief-print-brand">
                <Image
                    src={logoImage}
                    alt="Neighbourhood WatchDog logo"
                    width={52}
                    height={52}
                />

                <div>
                    <div className="brief-print-eyebrow">Officer report</div>
                    <h1>Neighbourhood WatchDog</h1>
                    <p>Situational brief · evidence summary</p>
                </div>
                </div>

                <div className="brief-print-meta">
                <strong>Generated</strong>
                <span>{formatBriefDate(brief.generated_at)}</span>

                <strong>Access</strong>
                <span>Officer-only document</span>
                </div>
            </header>

            <div className="brief-print-title-row">
                <div>
                <div className="brief-print-eyebrow">Critical incident</div>
                <h2>
                    {primaryAlert?.detection_type
                    ?.replaceAll("_", " ")
                    .toLowerCase()
                    .replace(/\b\w/g, (character) => character.toUpperCase()) ??
                    "Situational brief"}
                </h2>
                </div>

                <span className="brief-print-status">Active sequence</span>
            </div>

            <section className="brief-print-summary">
                {brief.summary}
            </section>

            <section className="brief-print-grid">
                <div>
                <label>Tracking subject</label>
                <span className="brief-print-mono">
                    {brief.tracking_subject_id}
                </span>
                </div>

                <div>
                <label>Trigger</label>
                <span>{brief.trigger.replaceAll("_", " ")}</span>
                </div>

                {primaryAlert && (
                <>
                    <div>
                    <label>Detection type</label>
                    <span>{primaryAlert.detection_type}</span>
                    </div>

                    <div>
                    <label>Confidence</label>
                    <span>
                        {(primaryAlert.confidence_score * 100).toFixed(1)}%
                    </span>
                    </div>

                    <div>
                    <label>Observed</label>
                    <span>{formatBriefDate(primaryAlert.observed_at)}</span>
                    </div>

                    <div>
                    <label>Initial camera</label>
                    <span>
                        {primaryAlert.camera_name} -{" "}
                        {primaryAlert.camera_location}
                    </span>
                    </div>
                </>
                )}
            </section>

            <section className="brief-print-section">
                <h3>Last known location</h3>

                <div className="brief-print-location">
                <strong>{brief.last_known_location.camera_name}</strong>
                <span>{brief.last_known_location.camera_location}</span>
                <small>
                    Observed{" "}
                    {formatBriefDate(brief.last_known_location.observed_at)}
                </small>
                </div>

                <p className="brief-print-location-note">
                Refer to the alert dashboard map for the live property location.
                </p>
            </section>

            <section className="brief-print-section">
                <h3>Cameras visited</h3>

                <ul className="brief-print-list">
                {brief.cameras.map((camera) => (
                    <li key={camera.camera_id}>
                    <span>
                        <strong>{camera.camera_name}</strong>
                        <br />
                        {camera.camera_location}
                    </span>

                    <span>{camera.property_id}</span>
                    </li>
                ))}
                </ul>
            </section>

            <section className="brief-print-section">
                <h3>Associated alerts</h3>

                <ul className="brief-print-list">
                {brief.alerts.map((alert) => (
                    <li key={alert.alert_id}>
                    <span>{alert.detection_type}</span>

                    <span>
                        {formatBriefDate(alert.observed_at)}
                        {" · "}
                        {(alert.confidence_score * 100).toFixed(1)}% confidence
                    </span>
                    </li>
                ))}
                </ul>
            </section>

            <section className="brief-print-section">
                <h3>Movement sightings</h3>

                <div className="brief-print-timeline">
                {brief.sightings.map((sighting) => (
                    <div className="brief-print-event" key={sighting.sighting_id}>
                    <strong>
                        #{sighting.sequence_no} · {sighting.camera_name}
                    </strong>

                    <span>
                        {sighting.camera_location}
                        {" · "}
                        {formatBriefDate(sighting.observed_at)}
                    </span>

                    {sighting.match_confidence != null && (
                        <span>
                        Match confidence:{" "}
                        {(sighting.match_confidence * 100).toFixed(1)}%
                        </span>
                    )}
                    </div>
                ))}
                </div>
            </section>

            <footer className="brief-print-footer">
                <span>Neighbourhood WatchDog</span>
                <span>Officer-only document</span>
            </footer>
        </article>

    )

}