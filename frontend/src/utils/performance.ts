/**
 * Performance Testing Utilities
 * Use these functions to measure and verify optimization improvements
 */

export class PerformanceMonitor {
  private marks: Map<string, number> = new Map();
  
  /**
   * Start timing an operation
   */
  start(label: string): void {
    this.marks.set(label, performance.now());
  }
  
  /**
   * End timing and log the duration
   */
  end(label: string, logToConsole = true): number {
    const startTime = this.marks.get(label);
    if (!startTime) {
      console.warn(`No start mark found for "${label}"`);
      return 0;
    }
    
    const duration = performance.now() - startTime;
    this.marks.delete(label);
    
    if (logToConsole) {
      const emoji = duration < 100 ? '✅' : duration < 300 ? '⚠️' : '❌';
      console.log(`${emoji} ${label}: ${duration.toFixed(2)}ms`);
    }
    
    return duration;
  }
  
  /**
   * Measure FPS during an operation
   */
  measureFPS(duration: number = 1000): Promise<number> {
    return new Promise((resolve) => {
      let frames = 0;
      const startTime = performance.now();
      
      const countFrame = () => {
        frames++;
        const elapsed = performance.now() - startTime;
        
        if (elapsed < duration) {
          requestAnimationFrame(countFrame);
        } else {
          const fps = (frames / elapsed) * 1000;
          console.log(`📊 Average FPS: ${fps.toFixed(2)}`);
          resolve(fps);
        }
      };
      
      requestAnimationFrame(countFrame);
    });
  }
  
  /**
   * Monitor memory usage (Chrome only)
   */
  getMemoryUsage(): { used: number; total: number; limit: number } | null {
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      return {
        used: Math.round(memory.usedJSHeapSize / 1048576), // MB
        total: Math.round(memory.totalJSHeapSize / 1048576), // MB
        limit: Math.round(memory.jsHeapSizeLimit / 1048576), // MB
      };
    }
    return null;
  }
  
  /**
   * Log memory usage
   */
  logMemoryUsage(): void {
    const memory = this.getMemoryUsage();
    if (memory) {
      console.log(`💾 Memory: ${memory.used}MB / ${memory.limit}MB (${((memory.used / memory.limit) * 100).toFixed(1)}%)`);
    }
  }
}

/**
 * Debounce function for performance optimization
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;
  
  return function(this: any, ...args: Parameters<T>) {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

/**
 * Throttle function for performance optimization
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean = false;
  
  return function(this: any, ...args: Parameters<T>) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

/**
 * Request Idle Callback wrapper with fallback
 */
export function requestIdleCallbackPolyfill(
  callback: () => void,
  options?: { timeout?: number }
): number {
  if ('requestIdleCallback' in window) {
    return window.requestIdleCallback(callback, options);
  }
  // Fallback to setTimeout
  return (window as any).setTimeout(callback, 1);
}

/**
 * Cancel Idle Callback wrapper with fallback
 */
export function cancelIdleCallbackPolyfill(id: number): void {
  if ('cancelIdleCallback' in window) {
    window.cancelIdleCallback(id);
  } else {
    clearTimeout(id);
  }
}

// Export singleton instance
export const perfMonitor = new PerformanceMonitor();
