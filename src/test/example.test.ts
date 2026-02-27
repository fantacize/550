import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import App from "../App";

describe("app", () => {
  it("shows the home heading", () => {
    render(<App />);
    expect(screen.getByText("Course Review Site")).toBeInTheDocument();
  });
});
