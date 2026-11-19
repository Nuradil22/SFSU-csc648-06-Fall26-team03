import { useState } from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

function TestComponent() {
    const [count, setCount] = useState(0);

    return (
        <button onClick={() => setCount(count + 1)}>
            Count: {count}
        </button>
    );
}

describe("React testing setup", () => {
    it("renders and updates state", async () => {
        const user = userEvent.setup();

        render(<TestComponent />);

        await user.click(
            screen.getByRole("button", { name: "Count: 0" })
        );

        expect(
            screen.getByRole("button", { name: "Count: 1" })
        ).toBeInTheDocument();
    });
});