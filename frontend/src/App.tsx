import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Layout } from "@/components/Layout";
import { Chat } from "@/pages/Chat";
import { Ingest } from "@/pages/Ingest";
import { Review } from "@/pages/Review";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Chat />} />
          <Route path="ingest" element={<Ingest />} />
          <Route path="review" element={<Review />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
