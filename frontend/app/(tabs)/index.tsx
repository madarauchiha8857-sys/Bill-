import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Image, Dimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import api from '../../src/api/client';
import { useAuthStore } from '../../src/store/authStore';

const { width } = Dimensions.get('window');

interface Product {
  id: string;
  name: string;
  price: number;
  original_price?: number;
  image_base64?: string;
  is_bestseller: boolean;
  is_new: boolean;
  rating: number;
}

export default function HomeScreen() {
  const { user } = useAuthStore();
  const [featuredProducts, setFeaturedProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFeaturedProducts();
  }, []);

  const loadFeaturedProducts = async () => {
    try {
      const response = await api.get('/products?is_bestseller=true');
      setFeaturedProducts(response.data.slice(0, 3));
    } catch (error) {
      console.error('Failed to load products:', error);
    } finally {
      setLoading(false);
    }
  };

  const navigateToProduct = (productId: string) => {
    router.push(`/product/${productId}`);
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Hero Section */}
        <LinearGradient
          colors={['#8B4513', '#A0522D']}
          style={styles.hero}
        >
          <View style={styles.heroContent}>
            <Text style={styles.heroSubtitle}>✦ Handcrafted in Pune</Text>
            <Text style={styles.heroTitle}>Sip the Goodness,{"\n"}Skip the Caffeine</Text>
            <Text style={styles.heroDescription}>
              Handcrafted from premium date seeds — a rich, aromatic cup that's 100% caffeine-free.
            </Text>
            <View style={styles.heroFeatures}>
              <View style={styles.heroFeature}>
                <Ionicons name="star" size={20} color="#FFD700" />
                <Text style={styles.heroFeatureText}>4.9 Rating</Text>
              </View>
              <View style={styles.heroFeature}>
                <Ionicons name="people" size={20} color="#FFD700" />
                <Text style={styles.heroFeatureText}>2,400+ Reviews</Text>
              </View>
            </View>
            <TouchableOpacity
              style={styles.heroButton}
              onPress={() => router.push('/shop')}
            >
              <Text style={styles.heroButtonText}>Shop Now</Text>
              <Ionicons name="arrow-forward" size={18} color="#8B4513" />
            </TouchableOpacity>
          </View>
        </LinearGradient>

        {/* Benefits Banner */}
        <View style={styles.benefitsBanner}>
          <View style={styles.benefitItem}>
            <Ionicons name="moon" size={24} color="#8B4513" />
            <Text style={styles.benefitText}>Better Sleep</Text>
          </View>
          <View style={styles.benefitItem}>
            <Ionicons name="flash-off" size={24} color="#8B4513" />
            <Text style={styles.benefitText}>Zero Jitters</Text>
          </View>
          <View style={styles.benefitItem}>
            <Ionicons name="leaf" size={24} color="#8B4513" />
            <Text style={styles.benefitText}>100% Natural</Text>
          </View>
        </View>

        {/* Featured Products */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Featured Products</Text>
            <TouchableOpacity onPress={() => router.push('/shop')}>
              <Text style={styles.seeAll}>See All</Text>
            </TouchableOpacity>
          </View>

          {loading ? (
            <View style={styles.loadingContainer}>
              <Text style={styles.loadingText}>Loading products...</Text>
            </View>
          ) : (
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.productsScroll}
            >
              {featuredProducts.map((product) => (
                <TouchableOpacity
                  key={product.id}
                  style={styles.productCard}
                  onPress={() => navigateToProduct(product.id)}
                >
                  <View style={styles.productImageContainer}>
                    {product.image_base64 ? (
                      <Image
                        source={{ uri: `data:image/jpeg;base64,${product.image_base64}` }}
                        style={styles.productImage}
                        resizeMode="cover"
                      />
                    ) : (
                      <View style={styles.productImagePlaceholder}>
                        <Ionicons name="cafe" size={48} color="#999" />
                      </View>
                    )}
                    {product.is_bestseller && (
                      <View style={[styles.badge, styles.badgeBestseller]}>
                        <Text style={styles.badgeText}>Bestseller</Text>
                      </View>
                    )}
                    {product.is_new && (
                      <View style={[styles.badge, styles.badgeNew]}>
                        <Text style={styles.badgeText}>New</Text>
                      </View>
                    )}
                  </View>
                  <View style={styles.productInfo}>
                    <Text style={styles.productName} numberOfLines={2}>
                      {product.name}
                    </Text>
                    <View style={styles.productRating}>
                      <Ionicons name="star" size={14} color="#FFD700" />
                      <Text style={styles.ratingText}>{product.rating}</Text>
                    </View>
                    <View style={styles.productPricing}>
                      <Text style={styles.productPrice}>₹{product.price}</Text>
                      {product.original_price && product.original_price > product.price && (
                        <Text style={styles.productOriginalPrice}>₹{product.original_price}</Text>
                      )}
                    </View>
                  </View>
                </TouchableOpacity>
              ))}
            </ScrollView>
          )}
        </View>

        {/* Why Dazeen Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Why Dazeen?</Text>
          <View style={styles.whyGrid}>
            <View style={styles.whyCard}>
              <Ionicons name="moon-outline" size={32} color="#8B4513" />
              <Text style={styles.whyTitle}>Better Sleep</Text>
              <Text style={styles.whyDescription}>Without caffeine, your nights are restful</Text>
            </View>
            <View style={styles.whyCard}>
              <Ionicons name="flash-outline" size={32} color="#8B4513" />
              <Text style={styles.whyTitle}>Natural Energy</Text>
              <Text style={styles.whyDescription}>Steady, jitter-free vitality</Text>
            </View>
            <View style={styles.whyCard}>
              <Ionicons name="heart-outline" size={32} color="#8B4513" />
              <Text style={styles.whyTitle}>Zero Acidity</Text>
              <Text style={styles.whyDescription}>Gentle on your stomach</Text>
            </View>
            <View style={styles.whyCard}>
              <Ionicons name="leaf-outline" size={32} color="#8B4513" />
              <Text style={styles.whyTitle}>Sustainable</Text>
              <Text style={styles.whyDescription}>Kind to body and earth</Text>
            </View>
          </View>
        </View>

        {/* CTA Section */}
        <View style={styles.ctaSection}>
          <Text style={styles.ctaTitle}>0% Caffeine, 0% Compromise</Text>
          <TouchableOpacity
            style={styles.ctaButton}
            onPress={() => router.push('/shop')}
          >
            <Text style={styles.ctaButtonText}>Explore Our Collection</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFBF5',
  },
  hero: {
    paddingHorizontal: 24,
    paddingVertical: 40,
    borderBottomLeftRadius: 24,
    borderBottomRightRadius: 24,
  },
  heroContent: {
    alignItems: 'center',
  },
  heroSubtitle: {
    color: '#FFD700',
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
  },
  heroTitle: {
    color: '#fff',
    fontSize: 28,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 12,
    lineHeight: 36,
  },
  heroDescription: {
    color: '#f5f5f5',
    fontSize: 15,
    textAlign: 'center',
    marginBottom: 24,
    lineHeight: 22,
  },
  heroFeatures: {
    flexDirection: 'row',
    gap: 24,
    marginBottom: 24,
  },
  heroFeature: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  heroFeatureText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  heroButton: {
    backgroundColor: '#fff',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 14,
    paddingHorizontal: 32,
    borderRadius: 24,
  },
  heroButtonText: {
    color: '#8B4513',
    fontSize: 16,
    fontWeight: 'bold',
  },
  benefitsBanner: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 20,
    backgroundColor: '#fff',
    marginTop: -12,
    marginHorizontal: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  benefitItem: {
    alignItems: 'center',
    gap: 6,
  },
  benefitText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#333',
  },
  section: {
    padding: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#333',
  },
  seeAll: {
    fontSize: 14,
    color: '#8B4513',
    fontWeight: '600',
  },
  loadingContainer: {
    paddingVertical: 40,
    alignItems: 'center',
  },
  loadingText: {
    color: '#999',
    fontSize: 14,
  },
  productsScroll: {
    paddingRight: 24,
  },
  productCard: {
    width: width * 0.65,
    marginRight: 16,
    backgroundColor: '#fff',
    borderRadius: 12,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  productImageContainer: {
    position: 'relative',
  },
  productImage: {
    width: '100%',
    height: 180,
  },
  productImagePlaceholder: {
    width: '100%',
    height: 180,
    backgroundColor: '#f5f5f5',
    justifyContent: 'center',
    alignItems: 'center',
  },
  badge: {
    position: 'absolute',
    top: 12,
    left: 12,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  badgeBestseller: {
    backgroundColor: '#FFD700',
  },
  badgeNew: {
    backgroundColor: '#FF6B6B',
  },
  badgeText: {
    fontSize: 11,
    fontWeight: 'bold',
    color: '#fff',
  },
  productInfo: {
    padding: 12,
  },
  productName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#333',
    marginBottom: 6,
    height: 40,
  },
  productRating: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginBottom: 8,
  },
  ratingText: {
    fontSize: 13,
    color: '#666',
  },
  productPricing: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  productPrice: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#8B4513',
  },
  productOriginalPrice: {
    fontSize: 14,
    color: '#999',
    textDecorationLine: 'line-through',
  },
  whyGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginTop: 16,
  },
  whyCard: {
    width: (width - 60) / 2,
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  whyTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 12,
    marginBottom: 6,
  },
  whyDescription: {
    fontSize: 13,
    color: '#666',
    textAlign: 'center',
  },
  ctaSection: {
    backgroundColor: '#8B4513',
    padding: 40,
    marginHorizontal: 24,
    marginBottom: 24,
    borderRadius: 16,
    alignItems: 'center',
  },
  ctaTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    textAlign: 'center',
    marginBottom: 20,
  },
  ctaButton: {
    backgroundColor: '#fff',
    paddingVertical: 14,
    paddingHorizontal: 32,
    borderRadius: 24,
  },
  ctaButtonText: {
    color: '#8B4513',
    fontSize: 16,
    fontWeight: 'bold',
  },
});