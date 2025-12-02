// Minimal test to verify React is working
import ReactDOM from "react-dom/client";

const TestApp = () => {
  return (
    <div style={{ padding: '50px', background: 'white', border: '5px solid red' }}>
      <h1 style={{ color: 'red', fontSize: '48px' }}>REACT IS WORKING!</h1>
      <p style={{ fontSize: '24px' }}>If you see this, React is rendering correctly.</p>
      <button style={{ padding: '20px', fontSize: '20px', background: 'green', color: 'white' }}>
        Test Button
      </button>
    </div>
  );
};

console.log('test-main.jsx loaded');
console.log('Root element:', document.getElementById("root"));

ReactDOM.createRoot(document.getElementById("root")).render(<TestApp />);
