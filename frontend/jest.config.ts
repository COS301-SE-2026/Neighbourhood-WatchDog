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
    '../tests/frontend/**/__tests__/**/*.test.[jt]s?(x)',
    '../tests/frontend/**/?(*.)+(spec|test).[jt]s?(x)',
  ],
};

export default config;
