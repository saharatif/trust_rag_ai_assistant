import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Layout } from "@/components/Layout";
import { Chat } from "@/pages/Chat";
import { Ingest } from "@/pages/Ingest";
import { Review } from "@/pages/Review";
import { ChatProvider } from "@/lib/ChatContext";

export default function App() {
  return (
    <ChatProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Chat />} />
            <Route path="ingest" element={<Ingest />} />
            <Route path="review" element={<Review />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ChatProvider>
  );
}
