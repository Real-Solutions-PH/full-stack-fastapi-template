/**
 * storage.ts picks its backend once at module load (Platform.OS), so each
 * test imports a fresh copy inside jest.isolateModules with the platform
 * and native module mocked per-case.
 */

type StorageModule = typeof import("@/lib/storage")

function loadStorage(platform: "ios" | "android" | "web"): StorageModule {
  let mod: StorageModule | undefined
  jest.isolateModules(() => {
    jest.doMock("react-native", () => ({ Platform: { OS: platform } }))
    mod = require("@/lib/storage")
  })
  if (!mod) throw new Error("storage module failed to load")
  return mod
}

const mockMmkvSet = jest.fn()
const mockMmkvGetString = jest.fn()
const mockMmkvRemove = jest.fn()
jest.mock("react-native-mmkv", () => ({
  createMMKV: () => ({
    set: mockMmkvSet,
    getString: mockMmkvGetString,
    remove: mockMmkvRemove,
  }),
}))

beforeEach(() => {
  jest.clearAllMocks()
})

describe("native platforms", () => {
  it("routes get/set/delete through MMKV", () => {
    const { mmkv } = loadStorage("ios")
    mockMmkvGetString.mockReturnValue("stored")

    mmkv.set("token", "abc")
    expect(mockMmkvSet).toHaveBeenCalledWith("token", "abc")
    expect(mmkv.getString("token")).toBe("stored")
    mmkv.remove("token")
    expect(mockMmkvRemove).toHaveBeenCalledWith("token")
  })
})

describe("web without localStorage (SSR / static export)", () => {
  const originalWindow = globalThis.window

  beforeEach(() => {
    // Simulate the SSR / static-export pass: no window, no localStorage.
    Object.defineProperty(globalThis, "window", {
      value: undefined,
      configurable: true,
      writable: true,
    })
  })

  afterEach(() => {
    Object.defineProperty(globalThis, "window", {
      value: originalWindow,
      configurable: true,
      writable: true,
    })
  })

  it("round-trips through the in-memory fallback and never touches MMKV", () => {
    expect(globalThis.window).toBeUndefined()
    const { mmkv } = loadStorage("web")

    expect(mmkv.getString("k")).toBeUndefined()
    mmkv.set("k", "v")
    expect(mmkv.getString("k")).toBe("v")
    mmkv.remove("k")
    expect(mmkv.getString("k")).toBeUndefined()

    expect(mockMmkvSet).not.toHaveBeenCalled()
    expect(mockMmkvGetString).not.toHaveBeenCalled()
  })
})

describe("web with localStorage", () => {
  let store: Record<string, string>

  beforeEach(() => {
    store = {}
    const localStorageStub = {
      getItem: (k: string) => (k in store ? store[k] : null),
      setItem: (k: string, v: string) => {
        store[k] = v
      },
      removeItem: (k: string) => {
        delete store[k]
      },
    }
    Object.defineProperty(globalThis, "window", {
      value: {},
      configurable: true,
      writable: true,
    })
    Object.defineProperty(globalThis, "localStorage", {
      value: localStorageStub,
      configurable: true,
      writable: true,
    })
  })

  afterEach(() => {
    delete (globalThis as Record<string, unknown>).window
    delete (globalThis as Record<string, unknown>).localStorage
  })

  it("round-trips through localStorage", () => {
    const { mmkv } = loadStorage("web")

    mmkv.set("session", "jwt")
    expect(store.session).toBe("jwt")
    expect(mmkv.getString("session")).toBe("jwt")
    mmkv.remove("session")
    expect(store.session).toBeUndefined()
    expect(mmkv.getString("session")).toBeUndefined()
  })
})

describe("mmkvStorage (zustand StateStorage adapter)", () => {
  it("maps missing keys to null, not undefined", () => {
    const { mmkvStorage } = loadStorage("web")
    expect(mmkvStorage.getItem("nope")).toBeNull()
    mmkvStorage.setItem("yes", "1")
    expect(mmkvStorage.getItem("yes")).toBe("1")
  })
})
