import { Outlet } from "@tanstack/react-router";
import type { ReactNode } from "react";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarInset,
  SidebarProvider,
  SidebarRail,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import SidebarUserFooter from "@/components/apx/sidebar-user-footer";

interface SidebarLayoutProps {
  children?: ReactNode;
}

function SidebarLayout({ children }: SidebarLayoutProps) {
  return (
    <SidebarProvider>
      <Sidebar>
        <SidebarHeader>
          <div
            className="bg-white rounded-lg mx-2 mt-2 overflow-hidden flex justify-center items-center"
            style={{ height: "54px", padding: "6px 0" }}
          >
            <img
              src="/sobeys-logo.png"
              alt="Sobeys"
              style={{
                width: "115%",
                maxWidth: "none",
                marginTop: "-1%",
              }}
            />
          </div>
          <span className="text-[10px] font-semibold text-sidebar-foreground/60 uppercase tracking-[0.12em] text-center py-1">
            Supply Chain Control Tower
          </span>
        </SidebarHeader>
        <SidebarContent>{children}</SidebarContent>
        <SidebarFooter>
          <SidebarUserFooter />
        </SidebarFooter>
        <SidebarRail />
      </Sidebar>
      <SidebarInset className="flex flex-col h-screen">
        <header className="sticky top-0 z-50 bg-background/80 backdrop-blur-sm border-b flex h-12 shrink-0 items-center gap-2 px-4">
          <SidebarTrigger className="-ml-1 cursor-pointer" />
          <div className="flex-1" />
          <div className="flex items-center gap-1.5 text-muted-foreground/60">
            <span className="text-[10px] font-medium">
              Powered by Databricks AI and Apps
            </span>
            <img
              src="/databricks-logo.jpg"
              alt="Databricks"
              className="h-5 rounded object-contain"
            />
          </div>
        </header>
        <div className="flex flex-1 justify-center overflow-auto">
          <div className="flex flex-1 flex-col gap-4 p-6 max-w-7xl">
            <Outlet />
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
export default SidebarLayout;
