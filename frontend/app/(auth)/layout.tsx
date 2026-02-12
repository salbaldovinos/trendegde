export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-muted/40 px-4">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold tracking-tight">TrendEdge</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          AI-Powered Futures Trading
        </p>
      </div>
      <div className="w-full max-w-[400px]">{children}</div>
    </div>
  )
}
