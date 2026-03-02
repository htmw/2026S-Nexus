import Navbar from "./Navbar";
import GreetingBar from "./GreetingBar";


export default function App() {
  return (
    <div style={{ minHeight: "100vh", background: "#fbfaf7" }}>
      <Navbar username="User" />
      <GreetingBar
        name="Vanessa"
        moodLabel="Balanced / neutral"
        dayStreak={0}
        entries={0}
        stabilityLabel="Very stable"
        consistencyLabel="0-day streak"
      />
    </div>
  );
}