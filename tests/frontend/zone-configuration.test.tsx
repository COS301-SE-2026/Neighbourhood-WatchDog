import { fireEvent, render, screen } from "@testing-library/react";
import CameraCard from "@/components/CameraCard";
import { CameraSettingsPanel } from "@/components/CameraSettingsPanel";

const mockUseCameraSettings = jest.fn();

jest.mock("@/hooks/use-camera-settings", () => ({
    useCameraSettings: () => mockUseCameraSettings(),
}));

jest.mock("@/components/ZoneEditor", () => ({
    ZoneEditor: () => <div data-testid="zone-editor" />,
}));

jest.mock("@/components/CameraCoverageEditor", () => ({
    CameraCoverageEditor: ({
        onChange,
    }: {
        onChange: (value: unknown) => void;
    }) => (
        <button
            type="button"
            onClick={() => onChange(undefined)}
        >
            Mock camera POV editor
        </button>
    ),
}));

jest.mock("@/components/camera-dropdown", () => {
    return function MockCameraDropdown() {
        return <div data-testid="camera-dropdown" />;
    };
});

jest.mock("@/lib/api/camera", () => ({
    getCameraCoverage: jest.fn().mockResolvedValue(null),
    saveCameraCoverage: jest.fn(),
    deleteCameraCoverage: jest.fn(),
}));

jest.mock("@/components/CameraFeed", () => {
    return function MockCameraFeed({
        onStreamStateChange,
    }: {
        onStreamStateChange?: (state: "unavailable") => void;
    }) {
        return (
            <button
                type="button"
                data-testid="camera-feed"
                onClick={() => onStreamStateChange?.("unavailable")}
            >
                mock feed
            </button>
        );
    };
});

function settingsState(zoneMutation: "adding" | "removing" | null) {
    return {
        settings: {
            camera_id: "00000000-0000-0000-0000-000000000001",
            confidence_threshold: 0.5,
            zones: [
                {
                    id: "zone-1",
                    camera_id: "00000000-0000-0000-0000-000000000001",
                    name: "Front gate",
                    polygon: [[0, 0], [1, 0], [1, 1]],
                },
            ],
        },
        loading: false,
        error: null,
        zoneMutation,
        updateThreshold: jest.fn(),
        createZone: jest.fn(),
        deleteZone: jest.fn(),
        refetch: jest.fn(),
    };
}

describe("zone configuration feedback", () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it("shows an applying message while a zone is being added", () => {
        mockUseCameraSettings.mockReturnValue(settingsState("adding"));

        render(
            <CameraSettingsPanel
                cameraId="00000000-0000-0000-0000-000000000001"
                userRole="PROPERTY_ADMIN"
                videoRef={{ current: null }}
                propertyLatitude={-25.7479}
                propertyLongitude={28.2293}
            />,
        );

        expect(screen.getByRole("status")).toHaveTextContent(
            "Applying new zone configuration",
        );
        expect(screen.getByText(/live stream will update in a few seconds/i)).toBeInTheDocument();
    });

    it("shows an applying message while a zone is being removed", () => {
        mockUseCameraSettings.mockReturnValue(settingsState("removing"));

        render(
            <CameraSettingsPanel
                cameraId="00000000-0000-0000-0000-000000000001"
                userRole="PROPERTY_ADMIN"
                videoRef={{ current: null }}
                propertyLatitude={-25.7479}
                propertyLongitude={28.2293}
            />,
        );

        expect(screen.getByRole("status")).toHaveTextContent(
            "Applying zone removal",
        );
    });

    it("keeps the CameraFeed mounted while the stream reconnects", () => {
        mockUseCameraSettings.mockReturnValue(settingsState(null));

        render(
            <CameraCard
                id="00000000-0000-0000-0000-000000000001"
                name="Front camera"
                location="Front gate"
                visibility="PRIVATE"
                enabled
                userRole="PROPERTY_ADMIN"
                onDeleted={jest.fn()}
            />,
        );

        fireEvent.click(screen.getByRole("button", { name: /open live stream/i }));
        const feed = screen.getByTestId("camera-feed");

        fireEvent.click(feed);

        expect(screen.getByTestId("camera-feed")).toBeInTheDocument();
        expect(screen.getByText("Live stream is reconnecting…")).toBeInTheDocument();
    });
});