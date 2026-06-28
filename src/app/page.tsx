import Navbar from "@/components/Navbar";
import HeroSection from "@/components/HeroSection";
import AboutSection from "@/components/AboutSection";
import HowItWorks from "@/components/HowItWorks";
import WhatWeProvide from "@/components/WhatWeProvide";
import CTASection from "@/components/CTASection";
import Footer from "@/components/Footer";

export default function Home() {
  return (
    <main>
      <Navbar />
      <HeroSection />
      <AboutSection />
      <HowItWorks />
      <WhatWeProvide />
      <CTASection />
      <Footer />
    </main>
  );
}
