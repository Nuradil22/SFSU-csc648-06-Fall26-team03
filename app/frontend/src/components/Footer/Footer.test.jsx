import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Footer from "./Footer";

function renderFooter(initialRoute = "/") {
    return render(
        <MemoryRouter initialEntries={[initialRoute]}>
            <Footer />
        </MemoryRouter>
    );
}

describe("Footer", () => {
    it("renders the Account and Resources sections", () => {
        renderFooter();

        expect(
            screen.getByRole("heading", {
                name: "Account"
            })
        ).toBeInTheDocument();

        expect(
            screen.getByRole("heading", {
                name: "Resources"
            })
        ).toBeInTheDocument();
    });

    it("renders all footer navigation links", () => {
        renderFooter();

        expect(
            screen.getByRole("link", {
                name: "Account Setup"
            })
        ).toBeInTheDocument();

        expect(
            screen.getByRole("link", {
                name: "Dashboard"
            })
        ).toBeInTheDocument();

        expect(
            screen.getByRole("link", {
                name: "SFSU Certificate Programs"
            })
        ).toBeInTheDocument();

        expect(
            screen.getByRole("link", {
                name: "About Projectory"
            })
        ).toBeInTheDocument();
    });

    it("uses the correct routes for each link", () => {
        renderFooter();

        expect(
            screen.getByRole("link", {
                name: "Account Setup"
            })
        ).toHaveAttribute("href", "/account/setup");

        expect(
            screen.getByRole("link", {
                name: "Dashboard"
            })
        ).toHaveAttribute("href", "/account/dashboard");

        expect(
            screen.getByRole("link", {
                name: "SFSU Certificate Programs"
            })
        ).toHaveAttribute("href", "/resources/certificates");

        expect(
            screen.getByRole("link", {
                name: "About Projectory"
            })
        ).toHaveAttribute("href", "/");
    });

    it("marks Account Setup as active on the setup route", () => {
        renderFooter("/account/setup");

        expect(
            screen.getByRole("link", {
                name: "Account Setup"
            })
        ).toHaveClass("active");

        expect(
            screen.getByRole("link", {
                name: "Dashboard"
            })
        ).not.toHaveClass("active");
    });

    it("marks Dashboard as active on the dashboard route", () => {
        renderFooter("/account/dashboard");

        expect(
            screen.getByRole("link", {
                name: "Dashboard"
            })
        ).toHaveClass("active");

        expect(
            screen.getByRole("link", {
                name: "Account Setup"
            })
        ).not.toHaveClass("active");
    });

    it("marks About Projectory as active on the home route", () => {
        renderFooter("/");

        expect(
            screen.getByRole("link", {
                name: "About Projectory"
            })
        ).toHaveClass("active");

        expect(
            screen.getByRole("link", {
                name: "SFSU Certificate Programs"
            })
        ).not.toHaveClass("active");
    });
});