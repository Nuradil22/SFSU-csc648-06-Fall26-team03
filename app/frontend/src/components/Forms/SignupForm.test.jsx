import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import SignupForm from "./SignupForm";

const {
    mockSignup,
    mockSaveAuth,
    mockNavigate
} = vi.hoisted(() => ({
    mockSignup: vi.fn(),
    mockSaveAuth: vi.fn(),
    mockNavigate: vi.fn()
}));

vi.mock("../../lib/api", () => ({
    signup: mockSignup,
    saveAuth: mockSaveAuth
}));

vi.mock("react-router-dom", () => ({
    useNavigate: vi.fn(() => mockNavigate)
}));

function renderSignupForm(props = {}) {
    return render(
        <SignupForm
            isReturningUser={false}
            setIsReturningUser={vi.fn()}
            {...props}
        />
    );
}

beforeEach(() => {
    vi.clearAllMocks();

    mockSignup.mockResolvedValue({
        token: "test-token",
        user: {
            name: "Test User",
            email: "user@example.com"
        }
    });
});

describe("SignupForm", () => {
    it("renders the signup form", () => {
        renderSignupForm();

        expect(
            screen.getByRole("heading", {
                name: "Create an Account:"
            })
        ).toBeInTheDocument();

        expect(
            screen.getByText("Your Journey Begins Here!")
        ).toBeInTheDocument();

        expect(
            screen.getByPlaceholderText("Name")
        ).toBeInTheDocument();

        expect(
            screen.getByPlaceholderText("Email")
        ).toBeInTheDocument();

        expect(
            screen.getByPlaceholderText("Password")
        ).toBeInTheDocument();

        expect(
            screen.getByRole("button", {
                name: "Sign Up"
            })
        ).toBeInTheDocument();
    });

    it("allows users to enter their account information", async () => {
        const user = userEvent.setup();

        renderSignupForm();

        const nameInput = screen.getByPlaceholderText("Name");
        const emailInput = screen.getByPlaceholderText("Email");
        const passwordInput = screen.getByPlaceholderText("Password");

        await user.type(nameInput, "Test User");
        await user.type(emailInput, "user@example.com");
        await user.type(passwordInput, "secure-password");

        expect(nameInput).toHaveValue("Test User");
        expect(emailInput).toHaveValue("user@example.com");
        expect(passwordInput).toHaveValue("secure-password");
    });

    it("switches to the login form", async () => {
        const user = userEvent.setup();
        const setIsReturningUser = vi.fn();

        renderSignupForm({
            isReturningUser: false,
            setIsReturningUser
        });

        await user.click(
            screen.getByRole("button", {
                name: "Already have an account?"
            })
        );

        expect(setIsReturningUser).toHaveBeenCalledWith(true);
    });

    it("switches back to the signup form when already returning", async () => {
        const user = userEvent.setup();
        const setIsReturningUser = vi.fn();

        renderSignupForm({
            isReturningUser: true,
            setIsReturningUser
        });

        await user.click(
            screen.getByRole("button", {
                name: "Already have an account?"
            })
        );

        expect(setIsReturningUser).toHaveBeenCalledWith(false);
    });

    it("signs up successfully and navigates to account setup", async () => {
        const user = userEvent.setup();

        renderSignupForm();

        await user.type(
            screen.getByPlaceholderText("Name"),
            "Test User"
        );

        await user.type(
            screen.getByPlaceholderText("Email"),
            "user@example.com"
        );

        await user.type(
            screen.getByPlaceholderText("Password"),
            "secure-password"
        );

        await user.click(
            screen.getByRole("button", {
                name: "Sign Up"
            })
        );

        await waitFor(() => {
            expect(mockSignup).toHaveBeenCalledWith({
                name: "Test User",
                email: "user@example.com",
                password: "secure-password"
            });
        });

        expect(mockSaveAuth).toHaveBeenCalledWith({
            token: "test-token",
            user: {
                name: "Test User",
                email: "user@example.com"
            }
        });

        expect(mockNavigate).toHaveBeenCalledWith(
            "/account/setup"
        );
    });

    it("displays an error when signup fails", async () => {
        const user = userEvent.setup();

        mockSignup.mockRejectedValue(
            new Error("Email is already registered")
        );

        renderSignupForm();

        await user.type(
            screen.getByPlaceholderText("Name"),
            "Test User"
        );

        await user.type(
            screen.getByPlaceholderText("Email"),
            "existing@example.com"
        );

        await user.type(
            screen.getByPlaceholderText("Password"),
            "secure-password"
        );

        await user.click(
            screen.getByRole("button", {
                name: "Sign Up"
            })
        );

        expect(
            await screen.findByText("Email is already registered")
        ).toBeInTheDocument();

        expect(mockSaveAuth).not.toHaveBeenCalled();
        expect(mockNavigate).not.toHaveBeenCalled();
    });

    it("disables the signup button while submitting", async () => {
        const user = userEvent.setup();
        let resolveSignup;

        mockSignup.mockImplementation(
            () =>
                new Promise((resolve) => {
                    resolveSignup = resolve;
                })
        );

        renderSignupForm();

        await user.type(
            screen.getByPlaceholderText("Name"),
            "Test User"
        );

        await user.type(
            screen.getByPlaceholderText("Email"),
            "user@example.com"
        );

        await user.type(
            screen.getByPlaceholderText("Password"),
            "secure-password"
        );

        await user.click(
            screen.getByRole("button", {
                name: "Sign Up"
            })
        );

        expect(
            screen.getByRole("button", {
                name: "Signing Up..."
            })
        ).toBeDisabled();

        resolveSignup({ token: "test-token" });

        await waitFor(() => {
            expect(
                screen.getByRole("button", {
                    name: "Sign Up"
                })
            ).not.toBeDisabled();
        });
    });

    it("does not submit when the name is missing", async () => {
        const user = userEvent.setup();

        renderSignupForm();

        await user.type(
            screen.getByPlaceholderText("Email"),
            "user@example.com"
        );

        await user.type(
            screen.getByPlaceholderText("Password"),
            "secure-password"
        );

        await user.click(
            screen.getByRole("button", {
                name: "Sign Up"
            })
        );

        expect(mockSignup).not.toHaveBeenCalled();
    });

    it("does not submit when the email is missing", async () => {
        const user = userEvent.setup();

        renderSignupForm();

        await user.type(
            screen.getByPlaceholderText("Name"),
            "Test User"
        );

        await user.type(
            screen.getByPlaceholderText("Password"),
            "secure-password"
        );

        await user.click(
            screen.getByRole("button", {
                name: "Sign Up"
            })
        );

        expect(mockSignup).not.toHaveBeenCalled();
    });

    it("does not submit when the password is missing", async () => {
        const user = userEvent.setup();

        renderSignupForm();

        await user.type(
            screen.getByPlaceholderText("Name"),
            "Test User"
        );

        await user.type(
            screen.getByPlaceholderText("Email"),
            "user@example.com"
        );

        await user.click(
            screen.getByRole("button", {
                name: "Sign Up"
            })
        );

        expect(mockSignup).not.toHaveBeenCalled();
    });
});