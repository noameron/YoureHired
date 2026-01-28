<script setup lang="ts">
import { ref, computed } from 'vue'
import AgentOutputCard from './AgentOutputCard.vue'

export interface AgentData {
  id: number
  name: string
  status: 'pending' | 'running' | 'complete' | 'error'
  output: string | null
  error?: string
}

const props = defineProps<{
  agents: AgentData[]
}>()

const currentSlide = ref(0)
const slideCount = computed(() => props.agents.length)

// Touch handling - using refs to properly scope state to component instance
const touchStartX = ref(0)
const touchCurrentX = ref(0)
const SWIPE_THRESHOLD = 50

function onTouchStart(e: TouchEvent) {
  touchStartX.value = e.touches[0].clientX
  touchCurrentX.value = touchStartX.value
}

function onTouchMove(e: TouchEvent) {
  touchCurrentX.value = e.touches[0].clientX
}

function onTouchEnd() {
  const diff = touchStartX.value - touchCurrentX.value
  if (Math.abs(diff) > SWIPE_THRESHOLD) {
    if (diff > 0) {
      nextSlide()
    } else {
      prevSlide()
    }
  }
}

function nextSlide() {
  if (currentSlide.value < slideCount.value - 1) {
    currentSlide.value++
  }
}

function prevSlide() {
  if (currentSlide.value > 0) {
    currentSlide.value--
  }
}

function goToSlide(index: number) {
  currentSlide.value = index
}

const slideTransform = computed(() => {
  return `translateX(-${currentSlide.value * 100}%)`
})
</script>

<template>
  <div class="carousel-container">
    <div
      class="carousel-viewport"
      @touchstart="onTouchStart"
      @touchmove="onTouchMove"
      @touchend="onTouchEnd"
    >
      <div
        class="carousel-slides"
        :style="{ transform: slideTransform }"
      >
        <div
          v-for="agent in agents"
          :key="agent.id"
          class="carousel-slide"
        >
          <AgentOutputCard
            :name="agent.name"
            :status="agent.status"
            :output="agent.output"
            :error="agent.error"
          />
        </div>
      </div>
    </div>

    <!-- Navigation arrows -->
    <button
      class="carousel-arrow arrow-left"
      :disabled="currentSlide === 0"
      aria-label="Previous agent"
      @click="prevSlide"
    >
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
      >
        <path
          d="M15 18l-6-6 6-6"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    </button>

    <button
      class="carousel-arrow arrow-right"
      :disabled="currentSlide === slideCount - 1"
      aria-label="Next agent"
      @click="nextSlide"
    >
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
      >
        <path
          d="M9 18l6-6-6-6"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    </button>

    <!-- Dot indicators -->
    <div class="carousel-dots">
      <button
        v-for="(_, index) in agents"
        :key="index"
        class="dot"
        :class="{ active: currentSlide === index }"
        :aria-label="`Go to agent ${index + 1}`"
        :aria-current="currentSlide === index ? 'true' : undefined"
        @click="goToSlide(index)"
      />
    </div>
  </div>
</template>

<style scoped>
.carousel-container {
  position: relative;
  width: 100%;
  max-width: 520px;
  margin: 0 auto;
}

.carousel-viewport {
  overflow: hidden;
  border-radius: var(--radius-2xl);
}

.carousel-slides {
  display: flex;
  transition: transform 0.4s ease-out;
}

.carousel-slide {
  min-width: 100%;
  padding: var(--space-1);
  box-sizing: border-box;
}

.carousel-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 40px;
  height: 40px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-full);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  transition: all var(--transition-fast);
  z-index: 10;
}

.carousel-arrow:hover:not(:disabled) {
  background: var(--bg-hover);
  border-color: var(--accent-primary);
  color: var(--accent-primary);
}

.carousel-arrow:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.carousel-arrow svg {
  width: 20px;
  height: 20px;
}

.arrow-left {
  left: -20px;
}

.arrow-right {
  right: -20px;
}

.carousel-dots {
  display: flex;
  justify-content: center;
  gap: var(--space-2);
  margin-top: var(--space-4);
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--border-secondary);
  border: none;
  cursor: pointer;
  padding: 0;
  transition: all var(--transition-base);
}

.dot:hover {
  background: var(--text-muted);
}

.dot.active {
  background: var(--accent-primary);
  box-shadow: 0 0 10px var(--accent-glow);
}

/* Mobile adjustments */
@media (max-width: 600px) {
  .carousel-arrow {
    width: 36px;
    height: 36px;
  }

  .arrow-left {
    left: var(--space-2);
  }

  .arrow-right {
    right: var(--space-2);
  }

  .carousel-arrow svg {
    width: 18px;
    height: 18px;
  }
}
</style>
