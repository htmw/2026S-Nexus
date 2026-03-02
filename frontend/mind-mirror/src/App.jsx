import Navbar from "./Navbar";

export default function App() {
  return (
    <div style={{ minHeight: "100vh", background: "#fbfaf7" }}>
      <Navbar active="Insights" username="User" />
    </div>
  );
}