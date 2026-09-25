import {
    deleteCameraCoverage,
    getCameraCoverage,
    saveCameraCoverage,
} from "@/lib/api/camera";
import { apiCall } from "@/lib/api/client";

jest.mock("@/lib/api/client", () => ({
    apiCall: jest.fn(),
}));

const mockedApiCall = jest.mocked(apiCall);

const CAMERA_ID =
    "00000000-0000-0000-0000-000000000001";

const COVERAGE = {
    origin_latitude: -25.7479,
    origin_longitude: 28.2293,
    coverage_bearing_degrees: 90,
    coverage_angle_degrees: 60,
    coverage_range_metres: 100,
};

describe("camera coverage API client", () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it("gets saved camera coverage", async () => {
        mockedApiCall.mockResolvedValueOnce(COVERAGE);

        const result = await getCameraCoverage(CAMERA_ID);

        expect(result).toEqual(COVERAGE);
        expect(mockedApiCall).toHaveBeenCalledWith(
            `/cameras/${CAMERA_ID}/coverage`,
            {
                method: "GET",
            },
        );
    });

    it("saves camera coverage", async () => {
        mockedApiCall.mockResolvedValueOnce(COVERAGE);

        const result = await saveCameraCoverage(
            CAMERA_ID,
            COVERAGE,
        );

        expect(result).toEqual(COVERAGE);
        expect(mockedApiCall).toHaveBeenCalledWith(
            `/cameras/${CAMERA_ID}/coverage`,
            {
                method: "PUT",
                body: COVERAGE,
            },
        );
    });

    it("deletes camera coverage", async () => {
        mockedApiCall.mockResolvedValueOnce(undefined);

        await deleteCameraCoverage(CAMERA_ID);

        expect(mockedApiCall).toHaveBeenCalledWith(
            `/cameras/${CAMERA_ID}/coverage`,
            {
                method: "DELETE",
            },
        );
    });
});