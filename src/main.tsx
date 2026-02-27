import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";

// mount the react app into the root div from index.html
const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error("root element not found");
}

const root = createRoot(rootElement);
root.render(<App />);
