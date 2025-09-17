import '@testing-library/jest-dom';

// Mock axios to avoid ES module issues
jest.mock('axios', () => ({
    create: jest.fn(() => ({
        get: jest.fn(),
        post: jest.fn(),
        patch: jest.fn(),
        delete: jest.fn(),
        interceptors: {
            request: { use: jest.fn() },
            response: { use: jest.fn() }
        }
    })),
    interceptors: {
        request: { use: jest.fn() },
        response: { use: jest.fn() }
    }
}));