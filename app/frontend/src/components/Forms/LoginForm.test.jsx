import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useNavigate } from "react-router-dom";
import { login, saveAuth } from "../../lib/api";
import LoginForm from "./LoginForm";

const {
    mockLogin,
    mockSaveAuth,
    mockNavigate
} = vi.hoisted(() => ({
    mockLogin: vi.fn(),
    mockSaveAuth: vi.fn(),
    mockNavigate: vi.fn()
}));

vi.mock("../../lib/api", () => ({
    login: mockLogin,
    saveAuth: mockSaveAuth
}));

vi.mock("react-router-dom", () => ({
    useNavigate: vi.fn(() => mockNavigate)
}));

function renderLoginForm(props = {}) {
    const defaultProps = {
        isReturningUser: true,
        setIsReturningUser: vi.fn()
    };

    return render(
        <LoginForm
            {...defaultProps}
            {...props}
        />
    );
}

beforeEach(() => {
    vi.clearAllMocks();
    mockLogin.mockResolvedValue({
        token: "test-token",
        user: {
            email: "user@example.com"
        }
    });
});

describe("LoginForm", () => {
    it("renders the login form", () => {
        renderLoginForm();

        expect(
            screen.getByRole("heading", {
                name: "Welcome Back!"
            })
        ).toBeInTheDocument();

        expect(
            screen.getByText(
                "Log in to continue your adventure"
            )
        ).toBeInTheDocument();

        expect(
            screen.getByPlaceholderText("Email")
        ).toBeInTheDocument();

        expect(
            screen.getByPlaceholderText("Password")
        ).toBeInTheDocument();

        expect(
            screen.getByRole("button", {
                name: "Log In"
            })
        ).toBeInTheDocument();
    });

    it("allows users to enter their email and password", async () => {
        const user = userEvent.setup();

        renderLoginForm();

        const emailInput = screen.getByPlaceholderText("Email");
        const passwordInput = screen.getByPlaceholderText("Password");

        await user.type(emailInput, "user@example.com");
        await user.type(passwordInput, "correct-password");

        expect(emailInput).toHaveValue("user@example.com");
        expect(passwordInput).toHaveValue("correct-password");
    });

    it("switches to the sign-up form", async () => {
        const user = userEvent.setup();
        const setIsReturningUser = vi.fn();

        renderLoginForm({
            isReturningUser: true,
            setIsReturningUser
        });

        await user.click(
            screen.getByRole("button", {
                name: "No account? Sign up here!"
            })
        );

        expect(setIsReturningUser).toHaveBeenCalledWith(false);
    });

    it("switches to the login form when already not returning", async () => {
        const user = userEvent.setup();
        const setIsReturningUser = vi.fn();

        renderLoginForm({
            isReturningUser: false,
            setIsReturningUser
        });

        await user.click(
            screen.getByRole("button", {
                name: "No account? Sign up here!"
            })
        );

        expect(setIsReturningUser).toHaveBeenCalledWith(true);
    });

    it("logs in successfully and navigates to the dashboard", async () => {
        const user = userEvent.setup();

        renderLoginForm();

        await user.type(
            screen.getByPlaceholderText("Email"),
            "user@example.com"
        );

        await user.type(
            screen.getByPlaceholderText("Password"),
            "correct-password"
        );

        await user.click(
            screen.getByRole("button", {
                name: "Log In"
            })
        );

        await waitFor(() => {
            expect(mockLogin).toHaveBeenCalledWith({
                email: "user@example.com",
                password: "correct-password"
            });
        });

        expect(mockSaveAuth).toHaveBeenCalledWith({
            token: "test-token",
            user: {
                email: "user@example.com"
            }
        });

        expect(mockNavigate).toHaveBeenCalledWith(
            "/account/dashboard"
        );
    });

    it("displays an error when login fails", async () => {
        const user = userEvent.setup();

        mockLogin.mockRejectedValue(
            new Error("Invalid email or password")
        );

        renderLoginForm();

        await user.type(
            screen.getByPlaceholderText("Email"),
            "wrong@example.com"
        );

        await user.type(
            screen.getByPlaceholderText("Password"),
            "wrong-password"
        );

        await user.click(
            screen.getByRole("button", {
                name: "Log In"
            })
        );

        expect(
            await screen.findByText("Invalid email or password")
        ).toBeInTheDocument();

        expect(mockSaveAuth).not.toHaveBeenCalled();
        expect(mockNavigate).not.toHaveBeenCalled();
    });

    it("disables the login button while submitting", async () => {
        const user = userEvent.setup();

        let resolveLogin;

        mockLogin.mockImplementation(
            () =>
                new Promise((resolve) => {
                    resolveLogin = resolve;
                })
        );

        renderLoginForm();

        await user.type(
            screen.getByPlaceholderText("Email"),
            "user@example.com"
        );

        await user.type(
            screen.getByPlaceholderText("Password"),
            "correct-password"
        );

        await user.click(
            screen.getByRole("button", {
                name: "Log In"
            })
        );

        expect(
            screen.getByRole("button", {
                name: "Logging In..."
            })
        ).toBeDisabled();

        resolveLogin({ token: "test-token" });

        await waitFor(() => {
            expect(
                screen.getByRole("button", {
                    name: "Log In"
                })
            ).not.toBeDisabled();
        });
    });

    it("does not submit when the email is missing", async () => {
        const user = userEvent.setup();

        renderLoginForm();

        await user.type(
            screen.getByPlaceholderText("Password"),
            "correct-password"
        );

        await user.click(
            screen.getByRole("button", {
                name: "Log In"
            })
        );

        expect(mockLogin).not.toHaveBeenCalled();
    });

    it("does not submit when the password is missing", async () => {
        const user = userEvent.setup();

        renderLoginForm();

        await user.type(
            screen.getByPlaceholderText("Email"),
            "user@example.com"
        );

        await user.click(
            screen.getByRole("button", {
                name: "Log In"
            })
        );

        expect(mockLogin).not.toHaveBeenCalled();
    });
});