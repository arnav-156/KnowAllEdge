import ReactDOM from "react-dom/client";
import App from "./App.jsx";
// ✅ I18N: Import i18n configuration (must be imported before App)
import './i18n/config';
// ✅ RTL: Import RTL styles for Arabic, Hebrew, etc.
import './styles/rtl.css';

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
