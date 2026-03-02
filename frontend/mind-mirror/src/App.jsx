import Navbar from "./Navbar";
import GreetingBar from "./GreetingBar";
import JournalEntryCard from "./JournalEntryCard";


// export default function App() {
//   return (
//     <div style={{ minHeight: "100vh", background: "#fbfaf7" }}>
//       <Navbar username="User" />
//       <GreetingBar
//         name="Vanessa"
//         moodLabel="Balanced / neutral"
//         dayStreak={0}
//         entries={0}
//         stabilityLabel="Very stable"
//         consistencyLabel="0-day streak"
//       />
//       <JournalEntryCard
//         onSubmitEntry={(entry) => {
//           console.log("Submitted entry:", entry);
//         }}
//       />
//     </div>
//   );
// }

// import Insights from "./Insights";

// export default function App() {
//   return (
//     <div style={{ minHeight: "100vh", background: "#fbfaf7" }}>
//       {/* keep Navbar if you want */}
//       <Navbar username="User" />
//       <Insights />
//     </div>
//   );
// }

import PastEntries from "./PastEntries";

export default function App() {
  return (
    <div style={{ minHeight: "100vh", background: "#fbfaf7" }}>
      {/* keep Navbar if you want */}
      <Navbar username="User" />
      <PastEntries />
    </div>
  );
}