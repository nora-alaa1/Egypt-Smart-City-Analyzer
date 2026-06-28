import { Brain, Mail, MapPin, Phone } from "lucide-react";
import Link from "next/link";

export default function Footer() {
  return (
    <footer className="border-t border-card-border py-12 px-4">
      <div className="container-wide">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="md:col-span-2">
            <Link href="/" className="flex items-center gap-2 mb-4">
              <Brain className="w-6 h-6 text-accent-purple" />
              <span className="font-heading text-lg font-bold">
                <span className="text-gradient">SheCodes</span>
                <span className="text-text-primary"> Cities</span>
              </span>
            </Link>
            <p className="text-text-secondary text-sm max-w-md">
              Empowering entrepreneurs and investors with AI-driven urban data
              analysis to find the perfect business location in Alexandria,
              Egypt.
            </p>
          </div>

          <div>
            <h4 className="font-heading font-semibold text-sm mb-4">Quick Links</h4>
            <div className="flex flex-col gap-2">
              <Link href="/" className="text-text-secondary text-sm hover:text-accent-purple transition-colors">Home</Link>
              <Link href="#about" className="text-text-secondary text-sm hover:text-accent-purple transition-colors">About</Link>
              <Link href="#how-it-works" className="text-text-secondary text-sm hover:text-accent-purple transition-colors">How It Works</Link>
              <Link href="/login" className="text-text-secondary text-sm hover:text-accent-purple transition-colors">Dashboard</Link>
            </div>
          </div>

          <div>
            <h4 className="font-heading font-semibold text-sm mb-4">Contact</h4>
            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-2 text-text-secondary text-sm">
                <MapPin size={14} className="text-accent-purple" />
                Alexandria, Egypt
              </div>
              <div className="flex items-center gap-2 text-text-secondary text-sm">
                <Mail size={14} className="text-accent-purple" />
                hello@shecodescities.com
              </div>
              <div className="flex items-center gap-2 text-text-secondary text-sm">
                <Phone size={14} className="text-accent-purple" />
                +20 123 456 7890
              </div>
            </div>
          </div>
        </div>

        <div className="border-t border-card-border mt-8 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-text-secondary text-xs">
            &copy; {new Date().getFullYear()} Egypt Smart City Analyzer. All rights reserved.
          </p>
          <div className="flex gap-4 text-text-secondary text-xs">
            <Link href="#" className="hover:text-accent-purple transition-colors">Privacy Policy</Link>
            <Link href="#" className="hover:text-accent-purple transition-colors">Terms of Service</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
