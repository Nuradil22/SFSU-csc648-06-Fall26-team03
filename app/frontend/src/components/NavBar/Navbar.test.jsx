import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import Navbar from "./Navbar";

const {
    mockGetToken,
    mockLogout,
    mockNavigate
} = vi.hoisted(() => ({
    mockGetToken: vi.fn(),
    mockLogout: vi.fn(),
    mockNavigate: vi.fn()
}));

vi.mock("../../lib/api", () => ({
    getToken: mockGetToken,
    logout: mockLogout
}));

vi.mock("react-router-dom", async () => {
    const actual = await vi.importActual("react-router-dom");

    return {
        ...actual,
        useNavigate: () => mockNavigate
    };
});

vi.mock("../../assets/light-logo-p.png", () => ({
    default: "light-logo.png"
}));

vi.mock("../../assets/dark-logo-P.png", () => ({
    default: "dark-logo.png"
}));

function renderNavbar(props = {}, route = "/") {
    return render(
        <MemoryRouter initialEntries={[route]}>
            <Navbar
                darkMode={false}
                setDarkMode={vi.fn()}
                {...props}
            />
        </MemoryRouter>
    );
}

beforeEach(() => {
    vi.clearAllMocks();

    mockGetToken.mockReturnValue(null);
    mockLogout.mockResolvedValue(undefined);
});

describe("Navbar", () => {
    it("renders the CareerGPS logo", () => {
        renderNavbar();

        const logo = screen.getByRole("img", {
            name: "CareerGPS logo"
        });

        expect(logo).toBeInTheDocument();
        expect(logo).toHaveAttribute(
            "src",
            "light-logo.png"
        );
    });

    it("renders the light logo when dark mode is disabled", () => {
        renderNavbar({
            darkMode: false
        });

        expect(
            screen.getByRole("img", {
                name: "CareerGPS logo"
            })
        ).toHaveAttribute("src", "light-logo.png");
    });

    it("renders the dark logo when dark mode is enabled", () => {
        renderNavbar({
            darkMode: true
        });

        expect(
            screen.getByRole("img", {
                name: "CareerGPS logo"
            })
        ).toHaveAttribute("src", "dark-logo.png");
    });

    it("shows Home and Log In when the user is logged out", () => {
        mockGetToken.mockReturnValue(null);

        renderNavbar();

        expect(
            screen.getByRole("link", {
                name: "Home"
            })
        ).toHaveAttribute("href", "/");

        expect(
            screen.getByRole("link", {
                name: "Log In"
            })
        ).toHaveAttribute("href", "/login");

        expect(
            screen.queryByRole("button", {
                name: "Log Out"
            })
        ).not.toBeInTheDocument();
    });

    it("shows Dashboard and Log Out when the user is logged in", () => {
        mockGetToken.mockReturnValue("test-token");

        renderNavbar();

        expect(
            screen.getByRole("link", {
                name: "Dashboard"
            })
        ).toHaveAttribute(
            "href",
            "/account/dashboard"
        );

        expect(
            screen.getByRole("button", {
                name: "Log Out"
            })
        ).toBeInTheDocument();

        expect(
            screen.queryByRole("link", {
                name: "Log In"
            })
        ).not.toBeInTheDocument();
    });

    it("renders the shared navigation links", () => {
        renderNavbar();

        expect(
            screen.getByRole("link", {
                name: "Career Roadmap"
            })
        ).toHaveAttribute("href", "/roadmap");

        expect(
            screen.getByRole("link", {
                name: "Explore Projects"
            })
        ).toHaveAttribute("href", "/explore");

        expect(
            screen.getByRole("link", {
                name: "Your Portfolio"
            })
        ).toHaveAttribute("href", "/portfolio");
    });

    it("marks the current route as active", () => {
        renderNavbar({}, "/explore");

        expect(
            screen.getByRole("link", {
                name: "Explore Projects"
            })
        ).toHaveClass("active");
    });

    it("does not mark an unrelated route as active", () => {
        renderNavbar({}, "/explore");

        expect(
            screen.getByRole("link", {
                name: "Career Roadmap"
            })
        ).not.toHaveClass("active");
    });

    it("toggles dark mode on", async () => {
        const user = userEvent.setup();
        const setDarkMode = vi.fn();

        renderNavbar({
            darkMode: false,
            setDarkMode
        });

        await user.click(
            screen.getByRole("button", {
                name: "🌙 Dark Mode"
            })
        );

        expect(setDarkMode).toHaveBeenCalledWith(true);
    });

    it("toggles dark mode off", async () => {
        const user = userEvent.setup();
        const setDarkMode = vi.fn();

        renderNavbar({
            darkMode: true,
            setDarkMode
        });

        await user.click(
            screen.getByRole("button", {
                name: "☀️ Light Mode"
            })
        );

        expect(setDarkMode).toHaveBeenCalledWith(false);
    });

    it("logs out and navigates to the login page", async () => {
        const user = userEvent.setup();

        mockGetToken.mockReturnValue("test-token");

        renderNavbar();

        await user.click(
            screen.getByRole("button", {
                name: "Log Out"
            })
        );

        await waitFor(() => {
            expect(mockLogout).toHaveBeenCalledTimes(1);
            expect(mockNavigate).toHaveBeenCalledWith(
                "/login"
            );
        });
    });

    it("navigates to login even when logout fails", async () => {
        const user = userEvent.setup();

        mockGetToken.mockReturnValue("test-token");
        mockLogout.mockRejectedValue(
            new Error("Logout request failed")
        );

        renderNavbar();

        await user.click(
            screen.getByRole("button", {
                name: "Log Out"
            })
        );

        await waitFor(() => {
            expect(mockNavigate).toHaveBeenCalledWith(
                "/login"
            );
        });
    });
});