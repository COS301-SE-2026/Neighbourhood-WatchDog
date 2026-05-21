/**
 * For a detailed explanation regarding each configuration property, visit:
 * https://jestjs.io/docs/configuration
 */

import type {Config} from 'jest';

const config: Config = {
  testEnvironment: 'jsdom',

  clearMocks: true,
  collectCoverage: true,
  coverageDirectory: '../tests/frontend/coverage',
  coverageProvider: 'v8',

  // Include repo-level tests directory so Jest discovers tests placed outside
  // the frontend package (e.g., /tests/frontend/...)
  roots: ["<rootDir>/../tests/frontend", "<rootDir>/src"],

  // Ensure modules can be resolved from the frontend package and the repository root
  moduleDirectories: ["node_modules", "<rootDir>/node_modules", "<rootDir>/../node_modules"],

  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],

  transform: {
    '^.+\\.tsx?$': ['ts-jest', {
      tsconfig: {
        jsx: 'react-jsx',
        esModuleInterop: true,
      },
    }],
  },

  testMatch: [
    // '../tests/frontend/**/__tests__/**/*.test.[jt]s?(x)',
    // '../tests/frontend/**/?(*.)+(spec|test).[jt]s?(x)',
    "<rootDir>/../tests/frontend/**/*.test.ts",
  ],
};

export default config;
