import { Link } from "react-router-dom";

export function NotFoundPage() { return <section><h1 className="text-2xl font-bold">Page not found</h1><Link className="mt-4 inline-block text-indigo-600" to="/">Return home</Link></section>; }
